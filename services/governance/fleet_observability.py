# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select, func
from typing import Dict, Any
# from libs.db.models.core_models import AgentNode, AgentStatus, FleetCluster, Project, ProjectStatus

class FleetObservability:
    def __init__(self, db: Any):
        self.db = db

    async def aggregate_fleet_metrics(self) -> Dict[str, Any]:
        """Collects real-time metrics for the entire fleet."""
        from sqlalchemy import select, func
        from libs.db.models.core_models import AgentNode, AgentStatus, FleetCluster, Project, ProjectStatus
        
        # 1. Agent Stats
        active_agents = await self.db.scalar(select(func.count(AgentNode.id)).where(AgentNode.status != AgentStatus.OFFLINE))
        idle_agents = await self.db.scalar(select(func.count(AgentNode.id)).where(AgentNode.status == AgentStatus.IDLE))
        busy_agents = await self.db.scalar(select(func.count(AgentNode.id)).where(AgentNode.status == AgentStatus.BUSY))
        quarantined = await self.db.scalar(select(func.count(AgentNode.id)).where(AgentNode.status == AgentStatus.QUARANTINED))
        
        # 2. Project Stats
        queued_projects = await self.db.scalar(select(func.count(Project.id)).where(Project.status == ProjectStatus.QUEUED)) or 0
        waiting_projects = await self.db.scalar(select(func.count(Project.id)).where(Project.status == ProjectStatus.WAITING)) or 0
        
        # 3. Budget & Cluster Stats
        total_budget_usage = await self.db.scalar(select(func.sum(FleetCluster.current_budget_usage))) or 0.0
        cluster_count = await self.db.scalar(select(func.count(FleetCluster.id))) or 0
        
        return {
            "active_agents": active_agents or 0,
            "idle_agents": idle_agents or 0,
            "busy_agents": busy_agents or 0,
            "quarantined_agents": quarantined or 0,
            "queued_projects": queued_projects + waiting_projects,
            "busy_ratio": (busy_agents / active_agents * 100) if active_agents and active_agents > 0 else 0,
            "budget_burn": total_budget_usage,
            "cluster_count": cluster_count
        }

    async def detect_fleet_drift(self) -> list:
        """Analyzes metric trends to detect deviations from desired state."""
        metrics = await self.aggregate_fleet_metrics()
        drifts = []
        if metrics["busy_ratio"] > 85.0:
            drifts.append({"type": "high_load", "message": "Fleet busy ratio is critically high.", "severity": "high"})
        if metrics["quarantined_agents"] > (metrics["active_agents"] * 0.2):
            drifts.append({"type": "quarantine_spike", "message": "Too many agents quarantined.", "severity": "critical"})
        return drifts

    async def emit_fleet_alerts(self):
        """Generates alerts based on critical thresholds."""
        from services.observability.logging import get_logger
        logger = get_logger("fleet_alerts")
        drifts = await self.detect_fleet_drift()
        for drift in drifts:
            logger.warning(f"ALERT [{drift['severity']}]: {drift['message']}")
