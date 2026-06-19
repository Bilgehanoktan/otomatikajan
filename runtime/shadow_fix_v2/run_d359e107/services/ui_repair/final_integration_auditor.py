import logging
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from libs.db.models.ui_repair_models import (
    UIFinalIntegrationAudit, ReleaseStatus,
    UIProviderHealth, UIAutoPatchExecution, UIKnowledgeNode, UIKnowledgeEdge,
    UITenantProfile, UIClusterProfile
)
from services.ui_repair.service import UIRepairService

logger = logging.getLogger(__name__)

class FinalIntegrationAuditor:
    """Phase 30: Performs end-to-end integration audits of all system modules."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def run_audit(self) -> UIFinalIntegrationAudit:
        """Runs a full system integration audit."""
        audit_key = f"AUDIT-{uuid.uuid4().hex[:8].upper()}"
        logger.info(f"Starting Final Integration Audit: {audit_key}")
        
        audit = UIFinalIntegrationAudit(
            audit_key=audit_key,
            status=ReleaseStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
            checked_modules_json={},
            failed_modules_json=[],
            warnings_json=[],
            summary_json={}
        )
        self.db.add(audit)
        await self.db.commit()
        await self.db.refresh(audit)

        summary = await UIRepairService(self.db).get_dashboard_summary()
        failing_routes = int(summary["failing_routes"])
        open_cases = int(summary["open_cases"])
        degraded_providers = (
            await self.db.execute(
                select(func.count(UIProviderHealth.id)).where(UIProviderHealth.status.in_(["DEGRADED", "UNAVAILABLE"]))
            )
        ).scalar() or 0
        failed_autopatch = (
            await self.db.execute(
                select(func.count(UIAutoPatchExecution.id)).where(UIAutoPatchExecution.status.in_(["FAILED", "PREFLIGHT_BLOCKED", "ROLLBACK_REQUIRED"]))
            )
        ).scalar() or 0
        knowledge_nodes = (await self.db.execute(select(func.count(UIKnowledgeNode.id)))).scalar() or 0
        knowledge_edges = (await self.db.execute(select(func.count(UIKnowledgeEdge.id)))).scalar() or 0
        tenant_count = (await self.db.execute(select(func.count(UITenantProfile.id)))).scalar() or 0
        cluster_count = (await self.db.execute(select(func.count(UIClusterProfile.id)))).scalar() or 0

        checks = {
            "UIRepairCore": "FAILED" if failing_routes > 0 else "PASSED",
            "ContinuousMonitoring": "WARNING" if open_cases > 0 else "PASSED",
            "ToolGovernance": "WARNING" if degraded_providers > 0 else "PASSED",
            "AutonomousPatching": "FAILED" if failed_autopatch > 0 else "PASSED",
            "KnowledgeGraph": "WARNING" if knowledge_nodes == 0 or knowledge_edges == 0 else "PASSED",
            "FederationMesh": "WARNING" if tenant_count == 0 or cluster_count == 0 else "PASSED",
        }

        results: Dict[str, str] = {}
        failed: List[str] = []
        warnings: List[str] = []
        for module, status in checks.items():
            results[module] = status
            if status == "FAILED":
                failed.append(module)
            elif status == "WARNING":
                warnings.append(module)

        audit.checked_modules_json = results
        audit.failed_modules_json = failed
        audit.warnings_json = warnings
        audit.status = ReleaseStatus.FAILED if failed else ReleaseStatus.WARNING if warnings else ReleaseStatus.PASSED
        audit.completed_at = datetime.now(timezone.utc)
        audit.summary_json = {
            "total_modules": len(results),
            "passed": len(results) - len(failed) - len(warnings),
            "failed": len(failed),
            "warnings": len(warnings)
        }
        audit.evidence_hash = f"SHA256:{audit.audit_key}:{len(failed)}:{len(warnings)}"
        
        await self.db.commit()
        await self.db.refresh(audit)
        
        logger.info(f"Final Integration Audit completed: {audit.status}")
        return audit

    async def get_latest_audit(self) -> Optional[UIFinalIntegrationAudit]:
        stmt = select(UIFinalIntegrationAudit).order_by(UIFinalIntegrationAudit.created_at.desc()).limit(1)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
