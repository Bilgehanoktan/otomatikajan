from sqlalchemy.orm import Session
from typing import List, Dict, Any
from libs.db.models.core_models import FleetCluster, AgentNode, AgentStatus, FleetStatus
from libs.db.repositories.fleet_repository import FleetClusterRepo, AgentNodeRepo

class FleetGovernor:
    def __init__(self, db: Session):
        self.db = db
        self.cluster_repo = FleetClusterRepo(db)
        self.agent_repo = AgentNodeRepo(db)

    def evaluate_fleet_health(self) -> Dict[str, Any]:
        """
        Scans the fleet for anomalies and returns a decision.
        """
        clusters = self.cluster_repo.list_clusters()
        decisions = []

        for cluster in clusters:
            # 1. Budget Pressure
            if cluster.budget_limit > 0 and (cluster.current_budget_usage / cluster.budget_limit > 0.95):
                decisions.append({
                    "cluster_id": cluster.id,
                    "action": "FREEZE_CLUSTER",
                    "reason": "Budget threshold breach (>95%)"
                })

            # 2. Agent Health (Quarantine rate)
            total_agents = self.db.query(AgentNode).filter(AgentNode.cluster_id == cluster.id).count()
            if total_agents > 0:
                quarantined = self.db.query(AgentNode).filter(
                    AgentNode.cluster_id == cluster.id,
                    AgentNode.status == AgentStatus.QUARANTINED
                ).count()
                
                if quarantined / total_agents > 0.3: # More than 30% agents quarantined
                    decisions.append({
                        "cluster_id": cluster.id,
                        "action": "ESCALATE_TO_META",
                        "reason": "High quarantine rate in cluster"
                    })

        return {
            "decisions": decisions,
            "status": "evaluated"
        }

    def apply_decision(self, decision: Dict[str, Any]):
        action = decision.get("action")
        cluster_id = decision.get("cluster_id")
        
        if action == "FREEZE_CLUSTER":
            cluster = self.cluster_repo.get_cluster(cluster_id)
            if cluster:
                cluster.status = FleetStatus.FROZEN
                self.db.commit()
        
        # Additional actions like REBALANCE_FLEET would involve moving agents
        # between clusters, which requires a more advanced infrastructure setup.
