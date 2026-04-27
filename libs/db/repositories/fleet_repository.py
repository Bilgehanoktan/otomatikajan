from sqlalchemy.orm import Session
from sqlalchemy import select, update, and_, func
from typing import List, Optional
import uuid
from datetime import datetime, timezone
from libs.db.models.core_models import (
    AgentNode, FleetCluster, FleetAssignment, 
    ProjectExecutionPlan, ProjectAgentAllocation,
    AgentStatus, AgentRole, FleetStatus
)
from libs.db.base import utcnow

class FleetRepository:
    def __init__(self, db: Session):
        self.db = db

    # --- Agent Methods ---
    def get_agent(self, agent_id: uuid.UUID) -> Optional[AgentNode]:
        return self.db.get(AgentNode, agent_id)

    def list_agents(self, role: Optional[str] = None) -> List[AgentNode]:
        query = select(AgentNode)
        if role:
            query = query.where(AgentNode.role == role)
        return list(self.db.scalars(query).all())

    def list_available_agents(self, role: Optional[AgentRole] = None) -> List[AgentNode]:
        # Filter by IDLE status specifically
        query = select(AgentNode).where(AgentNode.status == AgentStatus.IDLE)
        if role:
            query = query.where(AgentNode.role == role)
        return list(self.db.scalars(query).all())

    def save_agent(self, agent: AgentNode) -> AgentNode:
        self.db.add(agent)
        self.db.commit()
        self.db.refresh(agent)
        return agent

    def update_agent_status(self, agent_id: uuid.UUID, status: AgentStatus):
        self.db.execute(
            update(AgentNode)
            .where(AgentNode.id == agent_id)
            .values(status=status, updated_at=utcnow())
        )
        self.db.commit()

    # --- Cluster Methods ---
    def get_cluster(self, cluster_id: uuid.UUID) -> Optional[FleetCluster]:
        return self.db.get(FleetCluster, cluster_id)

    def list_clusters(self, status: Optional[FleetStatus] = None) -> List[FleetCluster]:
        query = select(FleetCluster)
        if status:
            query = query.where(FleetCluster.status == status)
        return list(self.db.scalars(query).all())

    # --- Assignment Methods ---
    def create_assignment(self, project_id: uuid.UUID, agent_id: uuid.UUID, assignment_type: str = "primary") -> FleetAssignment:
        assignment = FleetAssignment(
            project_id=project_id,
            agent_id=agent_id,
            assignment_type=assignment_type,
            status="active",
            started_at=utcnow()
        )
        self.db.add(assignment)
        
        self.db.execute(
            update(AgentNode)
            .where(AgentNode.id == agent_id)
            .values(status=AgentStatus.ASSIGNED)
        )
        
        self.db.commit()
        self.db.refresh(assignment)
        return assignment

    # --- Plan Methods ---
    def save_plan(self, plan: ProjectExecutionPlan) -> ProjectExecutionPlan:
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def get_plan_by_project(self, project_id: uuid.UUID) -> Optional[ProjectExecutionPlan]:
        return self.db.scalar(
            select(ProjectExecutionPlan).where(ProjectExecutionPlan.project_id == project_id)
        )

# For backward compatibility if needed by other services during transition
class AgentNodeRepo(FleetRepository): pass
class FleetClusterRepo(FleetRepository): pass
class FleetAssignmentRepo(FleetRepository): pass
class ProjectExecutionPlanRepo(FleetRepository): pass
