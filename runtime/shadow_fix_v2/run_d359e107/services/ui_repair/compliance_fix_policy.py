import logging
from libs.db.models.ui_repair_models import UIRepairSeverity, UISecurityRemediationPlan

logger = logging.getLogger(__name__)

class ComplianceFixPolicy:
    """Phase 22: Enforces safety guardrails for autonomous remediation."""
    
    @staticmethod
    def is_autofix_allowed(plan: UISecurityRemediationPlan) -> bool:
        """
        Determines if a remediation plan is eligible for autonomous execution.
        Returns False for HIGH/CRITICAL findings.
        """
        # 1. CRITICAL findings are NEVER auto-fixed.
        if plan.severity == UIRepairSeverity.CRITICAL.value:
            logger.warning(f"Auto-fix blocked: Finding {plan.finding_id} is CRITICAL.")
            return False
            
        # 2. HIGH findings require manual security review.
        if plan.severity == UIRepairSeverity.HIGH.value:
            logger.warning(f"Auto-fix blocked: Finding {plan.finding_id} is HIGH (Manual Review Required).")
            return False
            
        # 3. MEDIUM findings are allowed but require governance.
        if plan.severity == UIRepairSeverity.MEDIUM.value:
            # We allow the proposal generation, but orchestrator will enforce WAITING_APPROVAL
            return True
            
        # 4. LOW findings are always allowed.
        return True

    @staticmethod
    def requires_governance(plan: UISecurityRemediationPlan) -> bool:
        """Determines if the fix requires external governance approval."""
        if plan.severity in [UIRepairSeverity.MEDIUM.value, UIRepairSeverity.HIGH.value, UIRepairSeverity.CRITICAL.value]:
            return True
        return plan.requires_approval
