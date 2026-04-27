from sqlalchemy.orm import Session
import uuid
from typing import List, Optional
from libs.db.models.core_models import Project, ProjectStatus, AgentStatus, AgentRole, ProjectExecutionPlan
from libs.db.repositories.fleet_repository import (
    AgentNodeRepo, FleetClusterRepo, FleetAssignmentRepo, ProjectExecutionPlanRepo
)
from services.orchestration.fleet.agent_registry import AgentRegistry
from services.orchestration.fleet.project_orchestra_builder import ProjectOrchestraBuilder
from services.orchestration.fleet.fleet_budget_manager import FleetBudgetManager
from services.governance.lineage_service import LineageService
import asyncio
import threading

class FleetScheduler:
    def __init__(self, db: Session):
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
        # TODO: Implementation for Phase 12.2 (Dynamic rebalancing)
        pass

    def drain_cluster(self, cluster_id: uuid.UUID):
        """Prevents new assignments to a cluster and marks it for maintenance."""
        cluster = self.cluster_repo.get_cluster(cluster_id)
        if cluster:
            from libs.db.models.core_models import FleetStatus
            cluster.status = FleetStatus.DRAINING
            self.db.commit()
