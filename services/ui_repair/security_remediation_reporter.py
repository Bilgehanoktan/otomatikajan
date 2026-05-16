import logging
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from libs.db.models.ui_repair_models import (
    UISecurityRemediationPlan,
    UISecurityAutoFixAttempt,
    UIComplianceFixResult,
    RemediationStatus,
    UIRepairSeverity
)

logger = logging.getLogger(__name__)

class SecurityRemediationReporter:
    """Phase 22: Generates reports and metrics for security remediation activities."""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_remediation_summary(self) -> Dict[str, Any]:
        """Returns aggregated metrics for the remediation dashboard."""
        
        # 1. Total Plans by Status
        status_query = await self.db.execute(
            select(UISecurityRemediationPlan.status, func.count(UISecurityRemediationPlan.id))
            .group_by(UISecurityRemediationPlan.status)
        )
        status_counts = {status: count for status, count in status_query.all()}
        
        # 2. Total Plans by Severity
        severity_query = await self.db.execute(
            select(UISecurityRemediationPlan.severity, func.count(UISecurityRemediationPlan.id))
            .group_by(UISecurityRemediationPlan.severity)
        )
        severity_counts = {sev: count for sev, count in severity_query.all()}
        
        # 3. Success Rate
        total_attempts = await self.db.scalar(select(func.count(UISecurityAutoFixAttempt.id))) or 0
        successful_fixes = await self.db.scalar(
            select(func.count(UIComplianceFixResult.id)).where(UIComplianceFixResult.fixed == True)
        ) or 0
        
        success_rate = (successful_fixes / total_attempts * 100) if total_attempts > 0 else 0.0
        
        return {
            "status_distribution": status_counts,
            "severity_distribution": severity_counts,
            "total_plans": sum(status_counts.values()),
            "total_attempts": total_attempts,
            "successful_fixes": successful_fixes,
            "success_rate_pct": round(success_rate, 2)
        }

    async def list_residual_risks(self) -> List[Dict[str, Any]]:
        """Lists findings that were attempted but not fully fixed."""
        query = await self.db.execute(
            select(UIComplianceFixResult).where(UIComplianceFixResult.fixed == False)
        )
        results = query.scalars().all()
        return [
            {
                "finding_id": str(r.finding_id),
                "residual_risk": r.residual_risk,
                "created_at": r.created_at.isoformat()
            } for r in results
        ]
