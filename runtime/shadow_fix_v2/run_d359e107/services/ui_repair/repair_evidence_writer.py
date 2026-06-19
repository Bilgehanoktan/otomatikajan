from typing import Any, Dict, Optional, cast
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.ui_repair_models import UIRepairEvent, UIRepairCase, UIRepairAttempt, UIRepairPRReview, UIRepairVerifierRun, UIRepairGovernanceApproval
from services.observability.logging import get_logger

_log = get_logger("ui_repair_evidence")

class UIRepairEvidenceWriter:
    """
    Phase 4: Specialized writer for the UI repair evidence chain.
    Ensures every transition and agent action is audit-ready.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_event(
        self, 
        case_id: UUID, 
        event_type: str, 
        message: str, 
        status: Optional[str] = None, 
        attempt_id: Optional[UUID] = None,
        payload: Optional[Dict[str, Any]] = None
    ) -> UIRepairEvent:
        """Writes a traceable event to the UI repair audit log."""
        event = UIRepairEvent(
            case_id=case_id,
            attempt_id=attempt_id,
            event_type=event_type,
            status=status,
            message=message,
            payload_json=payload or {}
        )
        self.db.add(event)
        await self.db.flush()
        
        _log.info(f"UI_REPAIR_EVENT [{event_type}] for case {case_id}: {message}")
        return event

    async def record_stagehand_diagnostic(self, attempt: UIRepairAttempt, diagnostic: Dict[str, Any]):
        """Records the result of the Stagehand diagnostic phase."""
        a = cast(Any, attempt)
        a.stagehand_status = "COMPLETED"
        a.diagnostic_brief_json = diagnostic
        a.suspected_files_json = diagnostic.get("suspected_files", [])
        a.repair_instruction = diagnostic.get("repair_instruction", "No instruction generated.")
        
        await self.log_event(
            case_id=a.case_id,
            attempt_id=a.id,
            event_type="STAGEHAND_DIAGNOSTIC_COMPLETED",
            status="SUCCESS",
            message=f"Stagehand identified {len(a.suspected_files_json)} suspected files.",
            payload=diagnostic
        )

    async def record_open_swe_result(self, attempt: UIRepairAttempt, result: Dict[str, Any]):
        """Records the result of the OpenSWE repair phase."""
        a = cast(Any, attempt)
        if result.get("success"):
            a.open_swe_status = "COMPLETED"
            a.patch_path = result.get("patch_path")
            a.patch_summary = result.get("patch_summary")
            a.pr_url = result.get("pr_url")
            
            await self.log_event(
                case_id=a.case_id,
                attempt_id=a.id,
                event_type="OPEN_SWE_REPAIR_SUCCESS",
                status="SUCCESS",
                message=f"OpenSWE generated patch and opened PR: {a.pr_url}",
                payload=result
            )
        else:
            a.open_swe_status = "FAILED"
            a.error_message = result.get("error", "Unknown OpenSWE error")
            
            await self.log_event(
                case_id=a.case_id,
                attempt_id=a.id,
                event_type="OPEN_SWE_REPAIR_FAILED",
                status="FAILED",
                message=f"OpenSWE failed: {a.error_message}",
                payload=result
            )

    async def record_pr_review(self, attempt: UIRepairAttempt, result: Dict[str, Any]):
        """Records the result of the PR-Agent review phase."""
        a = cast(Any, attempt)
        
        review = UIRepairPRReview(
            case_id=a.case_id,
            attempt_id=a.id,
            pr_url=a.pr_url,
            status=result.get("status", "FAILED"),
            review_summary=result.get("review_summary"),
            describe_output_json=result.get("describe", {}),
            review_output_json=result.get("review", {}),
            improve_output_json=result.get("improve", {}),
            changed_files_json=result.get("changed_files", []),
            risk_level=result.get("risk_level", "LOW"),
            started_at=result.get("started_at"),
            finished_at=result.get("finished_at")
        )
        self.db.add(review)
        
        await self.log_event(
            case_id=a.case_id,
            attempt_id=a.id,
            event_type="PR_AGENT_REVIEW_COMPLETED",
            status=result.get("status"),
            message=f"PR-Agent review finished with status: {result.get('status')}. Risk Level: {review.risk_level}",
            payload=result
        )

    async def record_verifier_run(self, attempt: UIRepairAttempt, result: Dict[str, Any]):
        """Records the result of the Verifier Mesh phase."""
        a = cast(Any, attempt)
        
        gates = result.get("gates", {})
        run = UIRepairVerifierRun(
            case_id=a.case_id,
            attempt_id=a.id,
            pr_url=a.pr_url,
            status=result.get("status", "FAILED"),
            lint_status=gates.get("lint"),
            typecheck_status=gates.get("typecheck"),
            build_status=gates.get("build"),
            unit_test_status=gates.get("unit_tests"),
            playwright_status=gates.get("playwright_smoke"),
            smoke_status=gates.get("playwright_smoke"),
            route_regression_status=gates.get("route_regression"),
            result_summary_json=gates,
            logs_path=result.get("logs_path"),
            started_at=result.get("started_at"),
            finished_at=result.get("finished_at")
        )
        self.db.add(run)
        
        await self.log_event(
            case_id=a.case_id,
            attempt_id=a.id,
            event_type="VERIFIER_MESH_COMPLETED",
            status=result.get("status"),
            message=f"Verifier Mesh tests finished with status: {result.get('status')}",
            payload=result
        )

    async def record_governance_request(self, attempt: UIRepairAttempt, result: Dict[str, Any]):
        """Records the creation of a governance approval request."""
        a = cast(Any, attempt)
        
        policy = result.get("policy_decision", {})
        gov = UIRepairGovernanceApproval(
            case_id=a.case_id,
            attempt_id=a.id,
            pr_url=a.pr_url,
            approval_request_id=result.get("approval_request_id"),
            status=result.get("status", "REQUESTED"),
            risk_level=policy.get("risk_level"),
            auto_apply_allowed=policy.get("auto_apply_allowed", False),
            requires_operator_approval=policy.get("requires_operator_approval", True),
            requires_pr_agent_review=policy.get("requires_pr_agent_review", True),
            requires_verifier_mesh=policy.get("requires_verifier_mesh", True),
            policy_decision_json=policy
        )
        self.db.add(gov)
        
        await self.log_event(
            case_id=a.case_id,
            attempt_id=a.id,
            event_type="GOVERNANCE_APPROVAL_REQUESTED",
            status="SUCCESS",
            message=f"Approval request {gov.approval_request_id} created. Risk: {gov.risk_level}",
            payload=result
        )
