import logging
import uuid
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.ui_repair_models import (
    UISecurityRemediationPlan,
    UISecurityAutoFixAttempt,
    RemediationStatus,
    UIRepairSeverity
)
from services.ui_repair.compliance_fix_policy import ComplianceFixPolicy

logger = logging.getLogger(__name__)

class ComplianceAutoFixEngine:
    """Phase 22: Generates automated fix proposals (patches/PRs) for security findings."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.policy = ComplianceFixPolicy()

    async def propose_fix(self, plan: UISecurityRemediationPlan) -> Optional[UISecurityAutoFixAttempt]:
        """Generates an auto-fix proposal if allowed by policy."""
        if not self.policy.is_autofix_allowed(plan):
            logger.info(f"Skipping auto-fix for plan {plan.id} due to policy.")
            return None
            
        attempt = UISecurityAutoFixAttempt(
            id=uuid.uuid4(),
            remediation_plan_id=plan.id,
            finding_id=plan.finding_id,
            status=RemediationStatus.AUTO_FIX_RUNNING,
            fix_strategy=f"AUTONOMOUS_REPAIR_{plan.remediation_type.value}",
            posture_before_score=0.0, # Will be set by orchestrator
            started_at=datetime.now(timezone.utc)
        )
        
        # Simulate patch generation logic
        # In Phase 22, we generate the PROPOSAL.
        attempt.patch_path = f"/tmp/security_fixes/patch_{attempt.id}.patch"
        attempt.status = RemediationStatus.PATCH_GENERATED
        
        if self.policy.requires_governance(plan):
            attempt.status = RemediationStatus.GOVERNANCE_REQUESTED
            
        self.db.add(attempt)
        await self.db.commit()
        await self.db.refresh(attempt)
        
        return attempt
