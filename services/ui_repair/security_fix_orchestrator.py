import logging
import uuid
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from libs.db.models.ui_repair_models import (
    UISecurityPostureFinding,
    UISecurityRemediationPlan,
    UISecurityAutoFixAttempt,
    UIComplianceFixResult,
    RemediationStatus,
    UIRepairSeverity
)
from services.ui_repair.remediation_planner import RemediationPlanner
from services.ui_repair.compliance_autofix_engine import ComplianceAutoFixEngine
from services.ui_repair.posture_rescan_service import PostureRescanService
from services.ui_repair.remediation_evidence_writer import RemediationEvidenceWriter

logger = logging.getLogger(__name__)

class SecurityFixOrchestrator:
    """Phase 22: Orchestrates the end-to-end security remediation and compliance auto-fix workflow."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.planner = RemediationPlanner(db)
        self.autofix_engine = ComplianceAutoFixEngine(db)
        self.rescan_service = PostureRescanService(db)
        self.evidence_writer = RemediationEvidenceWriter(db)

    async def orchestrate_remediation(self, finding_id: uuid.UUID) -> Dict[str, Any]:
        """
        Runs the full remediation lifecycle for a finding:
        Plan -> Propose Fix -> Log Evidence.
        """
        # 1. Fetch Finding
        finding = await self.db.get(UISecurityPostureFinding, finding_id)
        if not finding:
            return {"status": "error", "message": "Finding not found"}
            
        # 2. Generate Plan
        plan = await self.planner.generate_plan(finding)
        await self.evidence_writer.log_event(
            finding_id=finding.id,
            plan_id=plan.id,
            event_type="REMEDIATION_PLAN_CREATED",
            message=f"Created remediation plan for {finding.control_key}",
            payload={"severity": plan.severity, "risk": plan.risk_level}
        )
        
        # 3. Handle CRITICAL/HIGH findings
        if plan.severity in [UIRepairSeverity.CRITICAL.value, UIRepairSeverity.HIGH.value]:
            plan.status = RemediationStatus.MANUAL_REQUIRED
            await self.db.commit()
            return {
                "status": "manual_review_required",
                "plan_id": str(plan.id),
                "severity": plan.severity
            }
            
        # 4. Propose Auto-Fix for LOW/MEDIUM
        attempt = await self.autofix_engine.propose_fix(plan)
        if attempt:
            await self.evidence_writer.log_event(
                finding_id=finding.id,
                plan_id=plan.id,
                attempt_id=attempt.id,
                event_type="AUTO_FIX_PROPOSED",
                message=f"Generated auto-fix proposal for {finding.control_key}",
                payload={"strategy": attempt.fix_strategy, "patch": attempt.patch_path}
            )
            return {
                "status": "fix_proposed",
                "plan_id": str(plan.id),
                "attempt_id": str(attempt.id)
            }
            
        return {
            "status": "planned",
            "plan_id": str(plan.id)
        }

    async def finalize_remediation(self, attempt_id: uuid.UUID) -> Dict[str, Any]:
        """
        Handles the post-apply phase: Rescan -> Certification Update -> Result Logging.
        (Note: In Phase 22, actual 'Apply' is still manual approval, this is for verification)
        """
        attempt = await self.db.get(UISecurityAutoFixAttempt, attempt_id)
        if not attempt:
            return {"status": "error", "message": "Attempt not found"}
            
        plan = await self.db.get(UISecurityRemediationPlan, attempt.remediation_plan_id)
        
        # 1. Run Rescan
        rescan_results = await self.rescan_service.run_rescan()
        attempt.posture_after_score = rescan_results["new_score"]
        
        # 2. Update Result
        result = UIComplianceFixResult(
            id=uuid.uuid4(),
            finding_id=attempt.finding_id,
            remediation_plan_id=attempt.remediation_plan_id,
            compliance_status_before="FAILED", # Snapshot from before
            compliance_status_after="PASSED" if rescan_results["new_score"] > attempt.posture_before_score else "FAILED",
            fixed=rescan_results["new_score"] > attempt.posture_before_score
        )
        
        attempt.status = RemediationStatus.FIX_VERIFIED if result.fixed else RemediationStatus.FAILED
        
        self.db.add(result)
        await self.db.commit()
        
        return {
            "status": attempt.status,
            "before_score": attempt.posture_before_score,
            "after_score": attempt.posture_after_score,
            "fixed": result.fixed
        }
