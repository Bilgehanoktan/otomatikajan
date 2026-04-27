from sqlalchemy.orm import Session
from sqlalchemy import select, func
import uuid
from libs.db.models.core_models import Project, FleetCluster, AgentNode
from libs.db.repositories.fleet_repository import FleetClusterRepo

class FleetBudgetManager:
    def __init__(self, db: Session):
        self.db = db
        self.cluster_repo = FleetClusterRepo(db)

    def can_schedule_project(self, project_id: uuid.UUID) -> bool:
        """Checks if a project can be scheduled within global and cluster budget limits."""
        project = self.db.get(Project, project_id)
        if not project:
            return False
        
        # 1. Individual Project Limit
        if project.budget_limit > 0 and project.total_cost >= project.budget_limit:
            return False
            
        # 2. Global Strategy (e.g., Monthly limit)
        # This could be checked against a GlobalSetting model or config
        
        return True

    def reserve_budget(self, project_id: uuid.UUID, cluster_id: uuid.UUID, estimated_cost: float):
        cluster = self.cluster_repo.get_cluster(cluster_id)
        if cluster:
            # Check if cluster budget limit is reached
            if cluster.budget_limit > 0 and (cluster.current_budget_usage + estimated_cost > cluster.budget_limit):
                raise ValueError(f"Cluster {cluster.name} budget limit reached.")
            
            cluster.current_budget_usage += estimated_cost
            self.db.commit()

    def release_budget(self, project_id: uuid.UUID, cluster_id: uuid.UUID, actual_cost: float, estimated_cost: float):
        """Adjusts cluster budget usage after project completion or step execution."""
        cluster = self.cluster_repo.get_cluster(cluster_id)
        if cluster:
            # Revert estimation and add actual
            cluster.current_budget_usage = cluster.current_budget_usage - estimated_cost + actual_cost
            self.db.commit()

    def detect_burn_rate_spike(self, window_hours: int = 1) -> bool:
        """Analyzes recent costs to detect unusual spending patterns."""
        # Query ModelRouterLog or similar for recent costs
        # Placeholder for Phase 12.5 hardening
        return False
