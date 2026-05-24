from typing import Dict, Any, Optional
from services.project_factory.models import PolicyPRReviewDecisionRequest
from services.project_factory.artifacts import load_policy_pr_review_report, write_policy_pr_status
from services.project_factory.policy_pr_review_logs import append_policy_pr_review_log

def execute_policy_pr_review_decision(
    proposal_id: str,
    request: PolicyPRReviewDecisionRequest,
    workspace_root: Optional[str] = None
) -> Dict[str, Any]:
    """
    Handles operator decision after review is complete.
    Transitions state to POLICY_READY_FOR_FINAL_DECISION or back to drafting.
    """
    report = load_policy_pr_review_report(proposal_id, workspace_root)
    if not report or report.get("proposal_id") != proposal_id:
        raise ValueError(f"No PR Review Report found for {proposal_id}")
        
    decision = request.decision.upper()
    valid_decisions = ["MARK_REVIEWED", "REQUEST_CHANGES", "BLOCK", "DEFER"]
    if decision not in valid_decisions:
        raise ValueError(f"Invalid decision: {decision}. Must be one of {valid_decisions}")

    if decision == "MARK_REVIEWED":
        if not request.risk_acknowledgement:
            raise ValueError("Cannot mark reviewed: risk acknowledgement is required.")
        if report.get("status") != "POLICY_PR_REVIEW_PASSED":
            raise ValueError("Cannot mark reviewed: PR Review status is not POLICY_PR_REVIEW_PASSED.")
        if report.get("blocking_findings"):
            raise ValueError("Cannot mark reviewed: PR Review has blocking findings.")
        
    if decision == "MARK_REVIEWED":
        new_status = "POLICY_READY_FOR_FINAL_DECISION"
    elif decision == "REQUEST_CHANGES":
        new_status = "POLICY_PR_REVIEW_REQUEST_CHANGES"
    elif decision == "BLOCK":
        new_status = "POLICY_PR_REVIEW_BLOCKED"
    else:
        new_status = "POLICY_PR_REVIEW_DEFERRED"
        
    # Write artifact
    write_policy_pr_status(proposal_id, {
        "proposal_id": proposal_id,
        "status": new_status,
        "operator_id": request.operator_id
    }, workspace_root)
    
    append_policy_pr_review_log(
        proposal_id, "OPERATOR_DECISION", request.operator_id, 
        {"decision": decision, "rationale": request.rationale, "new_status": new_status}, workspace_root
    )
    
    return {
        "proposal_id": proposal_id,
        "decision": decision,
        "new_status": new_status,
        "operator_id": request.operator_id
    }
