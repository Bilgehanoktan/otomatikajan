"""
Sovereign AGI — Phase 23
services/orchestration/quota_arbitrator.py
Decides if a task can be scheduled based on fleet-wide quotas and project priority.
"""
from __future__ import annotations
from typing import Dict, Any, Optional
from services.orchestration.fleet_manager import fleet_manager
from services.orchestration.federation_router import FederationTask

class QuotaViolationException(Exception):
    """Raised when a project exceeds its fleet-wide concurrency or budget limits."""
    pass

class AutonomyViolationException(Exception):
    """Raised when a task exceeds the defined Autonomy Envelope for a project."""
    pass

class QuotaArbitrator:
    def __init__(self):
        pass

    async def check_and_reserve(self, task: FederationTask, project_config: Dict[str, Any]) -> bool:
        """
        Validates task against Project Quotas and Autonomy Envelopes.
        """
        project_id = project_config.get("id")
        priority = project_config.get("priority", "medium")
        tier = project_config.get("isolation_tier", 2)
        limit = project_config.get("concurrency_limit", 5)
        envelope = project_config.get("autonomy_envelope", {})

        # 1. Register with Fleet Manager if not already tracked
        fleet_manager.register_workload(project_id, tier, priority, limit)

        # 2. Check Autonomy Envelope (Safety Gate)
        # If task is high-risk and auto_patch is disabled, we block or flag for approval
        if task.context.get("risk_score", 0) > envelope.get("max_risk_score", 0.5):
            if envelope.get("mode") == "advisory":
                 raise AutonomyViolationException(
                     f"Task risk ({task.context.get('risk_score')}) exceeds project envelope ({envelope.get('max_risk_score')}). "
                     "Switching to Human-In-The-Loop mandatory mode."
                 )

        # 3. Check Fleet Concurrency Quota (with Phase 24 Budget awareness)
        success = fleet_manager.increment_task(project_id, region="local-node")
        
        if not success:
            # Check if reason was budget
            snapshot = fleet_manager._active_workloads.get(project_id)
            if snapshot and snapshot.health == "BUDGET_EXHAUSTED":
                raise QuotaViolationException(f"Project {project_id} rejected due to BUDGET_EXHAUSTED.")
            
            # Default quota violation
            raise QuotaViolationException(
                f"Project {project_id} concurrency limit ({limit}) reached. "
                "Workload queued for priority resolution."
            )

        return True

    def release_quota(self, project_id: str):
        fleet_manager.decrement_task(project_id)

# Global Instance
quota_arbitrator = QuotaArbitrator()
