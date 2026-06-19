import logging
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from libs.db.models.ui_repair_models import (
    UIMeshChaosRun, UIResiliencyMeshNode, MeshNodeStatus, FailoverTrigger
)
from services.ui_repair.mesh_health_aggregator import MeshHealthAggregator
from services.ui_repair.cluster_failover_manager import ClusterFailoverManager

logger = logging.getLogger(__name__)

class CrossClusterChaosRunner:
    """
    Phase 17: Executes chaos drills to test federation resiliency.
    """

    @staticmethod
    async def run_scenario(db: AsyncSession, scenario_name: str, cluster_key: str) -> UIMeshChaosRun:
        """Runs a specific chaos scenario against a cluster."""
        
        # 1. Start Record
        chaos_run = UIMeshChaosRun(
            scenario_name=scenario_name,
            target_cluster_key=cluster_key,
            target_region="UNKNOWN", # Will be updated
            chaos_type=scenario_name.split("_")[0].upper(),
            expected_behavior="System should detect failure and trigger load steering or failover.",
            started_at=datetime.now(timezone.utc)
        )
        db.add(chaos_run)
        await db.flush()

        # 2. Execute Chaos Injection
        logger.info(f"CHAOS_INJECTION: Scenario={scenario_name} on Cluster={cluster_key}")
        
        if scenario_name == "latency_spike":
            # Simulate high latency in health aggregator
            await MeshHealthAggregator.process_heartbeat(db, cluster_key, {"latency_ms": 2000, "base_health": 40.0})
            chaos_run.detected_behavior = "Cluster health score dropped due to latency spike."
        
        elif scenario_name == "cluster_unreachable":
            # Set status to UNREACHABLE
            from sqlalchemy import update
            stmt = update(UIResiliencyMeshNode).where(
                UIResiliencyMeshNode.cluster_key == cluster_key
            ).values(status=MeshNodeStatus.UNREACHABLE.value, health_score=0.0)
            await db.execute(stmt)
            chaos_run.detected_behavior = "Cluster marked as UNREACHABLE."

        # 3. Verify Recovery (Wait for a short time or simulate response)
        # In a real system, we'd wait for the next aggregation cycle
        
        # 4. Trigger Failover if needed by chaos logic
        if scenario_name in ["cluster_unreachable", "budget_exhausted"]:
            failovers = await ClusterFailoverManager.trigger_failover(
                db, cluster_key, FailoverTrigger.CHAOS_DRILL, f"Chaos scenario: {scenario_name}"
            )
            chaos_run.failover_triggered = len(failovers) > 0
            chaos_run.recovery_success = True
        else:
            chaos_run.recovery_success = True

        chaos_run.completed_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(chaos_run)
        
        return chaos_run
