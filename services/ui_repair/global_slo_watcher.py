import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from libs.db.models.ui_repair_models import (
    UIGlobalSLOSnapshot, UIRepairAttempt, UIClusterFailoverEvent,
    UIRepairCase, UIResiliencyMeshNode
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

        # 2. Fetch Global MTTR (Simplified for Phase 17)
        # avg(completed_at - created_at)
        mttr = 1200.0 # Placeholder: 20 minutes average

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
        # (Assuming we count OperationalIncidents of type 'POLICY_VIOLATION')
        stmt_violations = select(func.count(OperationalIncident.id)).where(
            (OperationalIncident.incident_type == "POLICY_VIOLATION") &
            (OperationalIncident.created_at >= since)
        )
        violations = (await db.execute(stmt_violations)).scalar() or 0

        # 6. Create Snapshot
        snapshot = UIGlobalSLOSnapshot(
            tenant_key=tenant_key,
            federation_health_score=fed_health,
            global_mttr_s=mttr,
            global_detection_latency_s=45.0, # Placeholder
            repair_success_rate=repair_rate,
            failover_success_rate=fo_rate,
            policy_violation_count=violations,
            evidence_sync_success_rate=99.8, # Placeholder
        )
        
        db.add(snapshot)
        
        # 7. Check for Breach
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
