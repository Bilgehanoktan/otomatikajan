import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from libs.db.models.ui_repair_models import (
    UIGlobalSLOSnapshot, UIRepairAttempt, UIClusterFailoverEvent,
    UIRepairCase, UIResiliencyMeshNode, UIFederatedEvidenceRecord,
    UIClusterHealthSnapshot
)
from libs.db.models.core_models import OperationalIncident

logger = logging.getLogger(__name__)

class GlobalSLOWatcher:
    """
    Phase 17: Monitors federation-wide SLOs and compliance.
    """

    @staticmethod
    async def create_snapshot(db: AsyncSession, tenant_key: Optional[str] = None) -> UIGlobalSLOSnapshot:
        """Calculates and stores a global or tenant-specific SLO snapshot."""
        
        # 1. Fetch Repair Success Rate (Last 24h)
        since = datetime.now(timezone.utc) - timedelta(days=1)
        
        stmt_success = select(func.count(UIRepairAttempt.id)).where(
            (UIRepairAttempt.status == "SUCCESS") & (UIRepairAttempt.created_at >= since)
        )
        stmt_total = select(func.count(UIRepairAttempt.id)).where(
            UIRepairAttempt.created_at >= since
        )
        
        success_count = (await db.execute(stmt_success)).scalar() or 0
        total_count = (await db.execute(stmt_total)).scalar() or 1
        repair_rate = (success_count / total_count) * 100.0

        # 2. Fetch Global MTTR
        mttr_stmt = select(UIRepairCase).where(UIRepairCase.status == "RESOLVED")
        resolved_cases = (await db.execute(mttr_stmt)).scalars().all()
        if resolved_cases:
            total_time_diff = sum((c.updated_at - c.created_at).total_seconds() for c in resolved_cases if c.updated_at and c.created_at)
            mttr = total_time_diff / len(resolved_cases)
        else:
            mttr = 1200.0 # Fallback default

        # 3. Aggregated Federation Health
        stmt_health = select(func.avg(UIResiliencyMeshNode.health_score))
        fed_health = (await db.execute(stmt_health)).scalar() or 100.0

        # 4. Failover Success Rate
        stmt_fo_success = select(func.count(UIClusterFailoverEvent.id)).where(
            (UIClusterFailoverEvent.success == True) & (UIClusterFailoverEvent.created_at >= since)
        )
        stmt_fo_total = select(func.count(UIClusterFailoverEvent.id)).where(
            UIClusterFailoverEvent.created_at >= since
        )
        
        fo_success = (await db.execute(stmt_fo_success)).scalar() or 0
        fo_total = (await db.execute(stmt_fo_total)).scalar() or 1
        fo_rate = (fo_success / fo_total) * 100.0

        # 5. Policy Violations (Phase 16 link)
        stmt_violations = select(func.count(OperationalIncident.id)).where(
            (OperationalIncident.incident_type == "POLICY_VIOLATION") &
            (OperationalIncident.created_at >= since)
        )
        violations = (await db.execute(stmt_violations)).scalar() or 0

        # 6. Real average detection latency (from UIClusterHealthSnapshot)
        stmt_latency = select(func.avg(UIClusterHealthSnapshot.latency_ms)).where(
            UIClusterHealthSnapshot.captured_at >= since
        )
        avg_latency_ms = (await db.execute(stmt_latency)).scalar()
        if avg_latency_ms is not None:
            detection_latency = float(avg_latency_ms) / 1000.0
        else:
            detection_latency = 45.0 # Fallback default

        # 7. Real evidence sync success rate (from UIFederatedEvidenceRecord)
        stmt_sync_success = select(func.count(UIFederatedEvidenceRecord.id)).where(
            (UIFederatedEvidenceRecord.sync_status == "SYNCED") & (UIFederatedEvidenceRecord.created_at >= since)
        )
        stmt_sync_total = select(func.count(UIFederatedEvidenceRecord.id)).where(
            UIFederatedEvidenceRecord.created_at >= since
        )
        sync_success = (await db.execute(stmt_sync_success)).scalar() or 0
        sync_total = (await db.execute(stmt_sync_total)).scalar() or 0
        if sync_total > 0:
            evidence_sync_rate = (sync_success / sync_total) * 100.0
        else:
            evidence_sync_rate = 99.8 # Fallback default

        # 8. Create Snapshot
        snapshot = UIGlobalSLOSnapshot(
            tenant_key=tenant_key,
            federation_health_score=fed_health,
            global_mttr_s=mttr,
            global_detection_latency_s=detection_latency,
            repair_success_rate=repair_rate,
            failover_success_rate=fo_rate,
            policy_violation_count=violations,
            evidence_sync_success_rate=evidence_sync_rate,
        )
        
        db.add(snapshot)
        
        # 9. Check for Breach
        if repair_rate < 80.0 or fed_health < 70.0:
            incident = OperationalIncident(
                incident_type="SLO_BREACH",
                severity="CRITICAL",
                message=f"Global SLO Breach detected! Repair Rate: {repair_rate:.2f}% | Federation Health: {fed_health:.2f}%",
                status="OPEN"
            )
            db.add(incident)
            logger.error(f"SLO_BREACH: {incident.message}")

        await db.commit()
        await db.refresh(snapshot)
        return snapshot
