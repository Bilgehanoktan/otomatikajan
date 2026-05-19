import uuid
from typing import Any, List, Optional
from libs.db.models.core_models import (
    AgentRole,
    AgentStatus,
    Project,
    ProjectExecutionPlan,
    ProjectStatus,
)
from libs.db.repositories.fleet_repository import ProjectExecutionPlanRepo
from services.orchestration.fleet.agent_registry import AgentRegistry
from services.orchestration.fleet.project_orchestra_builder import ProjectOrchestraBuilder
from services.orchestration.fleet.fleet_budget_manager import FleetBudgetManager
from services.governance.lineage_service import LineageService
import asyncio
import threading

class FleetScheduler:
    def __init__(self, db: Any):
        from libs.db.repositories.fleet_repository import (
            AgentNodeRepo, FleetClusterRepo, FleetAssignmentRepo
        )
        self.db = db
        self.agent_repo = AgentNodeRepo(db)
        self.cluster_repo = FleetClusterRepo(db)
        self.assignment_repo = FleetAssignmentRepo(db)
        self.plan_repo = ProjectExecutionPlanRepo(db)
        
        self.registry = AgentRegistry(db)
        self.builder = ProjectOrchestraBuilder()
        self.budget_manager = FleetBudgetManager(db)

    def _fire_and_forget_logging(self, coro):
        """Safely runs an async logging coroutine in the background."""
        def run():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(coro)
                loop.close()
            except Exception as e:
                print(f"[FleetScheduler] Background logging failed: {e}")

        threading.Thread(target=run, daemon=True).start()

    def schedule_project(self, project_id: uuid.UUID) -> bool:
        """Entry point to start the orchestration for a project."""
        project = self.db.get(Project, project_id)
        if not project or project.status != ProjectStatus.PENDING:
            return False

        # 1. Budget Check
        if not self.budget_manager.can_schedule_project(project_id):
            project.status = ProjectStatus.WAITING
            project.report += "\n[Fleet] Budget limit reached. Scheduling deferred."
            
            # Phase 12: Record Budget Block
            self._fire_and_forget_logging(LineageService.log_fleet_event(
                event_type="BUDGET_BLOCK",
                target_id=str(project_id),
                details=f"Project {project_id} deferred due to budget limits."
            ))
            
            self.db.commit()
            return False

        # 2. Build Plan
        required_roles = self.builder.infer_required_roles(project)
        estimated_cost = self.builder.estimate_team_cost(required_roles)
        
        plan = ProjectExecutionPlan(
            project_id=project_id,
            required_roles=[r.value for r in required_roles],
            estimated_cost=estimated_cost,
            status="draft"
        )
        self.plan_repo.save_plan(plan)
        
        # 3. Allocation
        success = self.allocate_agents(project_id)
        if success:
            project.status = ProjectStatus.QUEUED
            plan.status = "allocated"
            self.db.commit()
            return True
        else:
            project.status = ProjectStatus.WAITING
            plan.status = "resource_wait"
            self.db.commit()
            return False

    def allocate_agents(self, project_id: uuid.UUID) -> bool:
        """Finds and assigns suitable agents for the project's required roles."""
        plan = self.plan_repo.get_plan_by_project(project_id)
        if not plan:
            return False
        
        allocated_agents = []
        try:
            for role_name in plan.required_roles:
                role = AgentRole(role_name)
                candidate = self.registry.get_best_candidate(role)
                
                if not candidate:
                    # Rolling back partial allocation if we can't find a full team
                    # (Simplified for Phase 12 - in production we'd use a transaction)
                    raise ValueError(f"No available candidate for role: {role_name}")
                
                allocated_agents.append(candidate)
            
            # All agents found, perform assignments
            for agent in allocated_agents:
                self.assignment_repo.create_assignment(project_id, agent.id)
                
                # Phase 12: Record Assignment
                self._fire_and_forget_logging(LineageService.log_fleet_event(
                    event_type="AGENT_ASSIGNED",
                    target_id=str(agent.id),
                    details=f"Agent {agent.name} assigned to project {project_id}",
                    meta={"project_id": str(project_id), "role": agent.role.value}
                ))
            
            return True
        except ValueError:
            return False

    def rebalance_fleet(self):
        """Redistributes load if some clusters are overloaded."""
        from sqlalchemy import select
        from libs.db.models.core_models import FleetCluster, AgentNode
        
        clusters = self.db.scalars(select(FleetCluster)).all()
        overloaded = []
        underloaded = []
        
        for cluster in clusters:
            usage_pct = (cluster.current_budget_usage / cluster.budget_limit) if cluster.budget_limit > 0 else 0
            if usage_pct > 0.85:
                overloaded.append(cluster)
            elif usage_pct < 0.4:
                underloaded.append(cluster)
                
        if not overloaded or not underloaded:
            return
            
        for overloaded_cluster in overloaded:
            for underloaded_cluster in underloaded:
                idle_agents = self.db.scalars(
                    select(AgentNode)
                    .where(AgentNode.cluster_id == underloaded_cluster.id)
                    .where(AgentNode.status == AgentStatus.IDLE)
                ).all()
                
                for agent in idle_agents:
                    agent.cluster_id = overloaded_cluster.id
                    
                    self._fire_and_forget_logging(LineageService.log_fleet_event(
                        event_type="FLEET_REBALANCED",
                        target_id=str(agent.id),
                        details=f"Agent {agent.name} moved to overloaded cluster {overloaded_cluster.name}"
                    ))
                    
                    # Basic capacity limit check
                    from sqlalchemy import func
                    current_count = self.db.scalar(select(func.count(AgentNode.id)).where(AgentNode.cluster_id == overloaded_cluster.id))
                    # Using arbitrary logic: if agent count exceeds parallel projects limit * 3
                    if current_count is not None and current_count >= overloaded_cluster.max_parallel_projects * 3:
                        break
                        
        self.db.commit()

    def release_project_agents(self, project_id: uuid.UUID, success: Optional[bool] = None):
        """Release all agents assigned to a project."""
        from libs.db.models.core_models import FleetAssignment
        from sqlalchemy import select
        from libs.db.base import utcnow
        
        assignments = self.db.scalars(
            select(FleetAssignment)
            .where(FleetAssignment.project_id == project_id)
            .where(FleetAssignment.status == "active")
        ).all()
        
        for assignment in assignments:
            assignment.status = "released"
            assignment.ended_at = utcnow()
            
            agent = self.agent_repo.get_agent(assignment.agent_id)
            if agent:
                agent.status = AgentStatus.IDLE
                
                # Phase 12.2 Reputation Update
                if success is not None:
                    self.registry.update_agent_reputation(agent.id, success=success)
                
            self._fire_and_forget_logging(LineageService.log_fleet_event(
                event_type="AGENT_RELEASED",
                target_id=str(assignment.agent_id),
                details=f"Agent released from project {project_id} (Success: {success})"
            ))
        self.db.commit()

    def drain_cluster(self, cluster_id: uuid.UUID):
        """Prevents new assignments to a cluster and marks it for maintenance."""
        cluster = self.cluster_repo.get_cluster(cluster_id)
        if cluster:
            from libs.db.models.core_models import FleetStatus
            cluster.status = FleetStatus.DRAINING
            self.db.commit()
