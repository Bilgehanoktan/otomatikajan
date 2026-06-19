import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from libs.db.models.ui_repair_models import (
    UIResiliencyMeshNode, UIClusterFailoverEvent, UIRepairCase,
    MeshNodeStatus, FailoverTrigger, WorkloadType
)
from libs.db.models.core_models import SovereignEvidence
from services.ui_repair.global_load_steering import GlobalLoadSteering

logger = logging.getLogger(__name__)

class ClusterFailoverManager:
    """
    Phase 17: Manages the failover lifecycle for repair workloads.
    """

    @staticmethod
    async def trigger_failover(
        db: AsyncSession, 
        source_cluster: str, 
        trigger: FailoverTrigger, 
        reason: str
    ) -> List[UIClusterFailoverEvent]:
        """
        Triggers failover for all projects/workloads on a degraded cluster.
        """
        logger.warning(f"FAILOVER_TRIGGERED: Cluster={source_cluster} | Trigger={trigger} | Reason={reason}")
        
        # 1. Fetch active cases on this cluster
        stmt = select(UIRepairCase).where(
            (UIRepairCase.cluster_key == source_cluster) &
            (UIRepairCase.status.in_(["OPEN", "PENDING_REPAIR", "RUNNING_REPAIR"]))
        )
        cases = list((await db.execute(stmt)).scalars().all())
        
        events = []
        steering = GlobalLoadSteering(db)

        for case in cases:
            # 2. Select a target cluster for this specific case/tenant
            target_cluster, steering_reason = await steering.select_best_cluster(
                tenant_key=case.tenant_key,
                project_key=case.project_key,
                workload_type=WorkloadType.OPENSWE_REPAIR, # General repair workload
                source_cluster=source_cluster
            )

            if target_cluster:
                # 3. Create Event
                event = UIClusterFailoverEvent(
                    source_cluster_key=source_cluster,
                    target_cluster_key=target_cluster,
                    tenant_key=case.tenant_key,
                    reason=f"{reason} | Case {case.id} moved.",
                    trigger_type=trigger.value,
                    severity="high",
                    decision_json={"steering_reason": steering_reason},
                    success=True,
                    started_at=datetime.now(timezone.utc),
                    completed_at=datetime.now(timezone.utc)
                )
                db.add(event)

                # 4. Migrate Case
                case.cluster_key = target_cluster
                
                # 5. Record Evidence
                evidence = SovereignEvidence(
                    evidence_type="CLUSTER_FAILOVER",
                    severity="high",
                    payload={
                        "case_id": str(case.id),
                        "source": source_cluster,
                        "target": target_cluster,
                        "trigger": trigger.value,
                        "reason": reason
                    }
                )
                db.add(evidence)
                
                await db.flush()
                event.evidence_hash = "SHA256:FAKE_HASH_FOR_PHASE_17" # Real hashing in Phase 16 ledger
                events.append(event)
            else:
                logger.error(f"FAILOVER_FAILED: No target cluster for Case {case.case_id}")
                # We could create an OperationalIncident here
        
        # 6. Update Source Cluster Status
        update_stmt = update(UIResiliencyMeshNode).where(
            UIResiliencyMeshNode.cluster_key == source_cluster
        ).values(status=MeshNodeStatus.FAILOVER_ACTIVE.value)
        await db.execute(update_stmt)

        await db.commit()
        return events
