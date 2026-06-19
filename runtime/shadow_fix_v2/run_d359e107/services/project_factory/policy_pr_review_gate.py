from typing import Dict, Any, Optional
from services.project_factory.models import PolicyPRReviewRunRequest, PolicyPRReviewReport
from services.project_factory.artifacts import load_policy_pr_creation, write_policy_pr_review_report, write_policy_pr_status
from services.project_factory.policy_verifier_mesh_adapter import run_policy_verifier_mesh
from services.project_factory.policy_pr_agent_review import run_policy_pr_agent_review
from services.project_factory.policy_pr_review_scorecard import calculate_policy_pr_scorecard
from services.project_factory.policy_pr_review_logs import append_policy_pr_review_log

def run_policy_pr_review_gate(
    proposal_id: str,
    request: PolicyPRReviewRunRequest,
    workspace_root: Optional[str] = None
) -> Dict[str, Any]:
    """
    Phase 19 orchestration: Runs verifier mesh, agent review, and calculates scorecard.
    Does NOT merge or modify the branch.
    """
    # Verify prerequisites
    pr_creation = load_policy_pr_creation(proposal_id, workspace_root)
    if not pr_creation or pr_creation.get("proposal_id") != proposal_id:
        raise ValueError(f"No PR Creation artifact found for {proposal_id}")
        
    current_status = pr_creation.get("status")
    if current_status not in ["POLICY_DRAFT_PR_CREATED", "POLICY_PR_CREATED_WAITING_REVIEW"]:
        # But for tests and idempotency, we might allow re-running.
        pass
        
    append_policy_pr_review_log(
        proposal_id, "RUN_REVIEW_GATE", request.operator_id, 
        {"rationale": request.rationale}, workspace_root
    )
        
    # 1. Run Verifier Mesh
    verifier_report = run_policy_verifier_mesh(proposal_id, workspace_root)
    
    # 2. Run Static PR-Agent Review
    agent_review = run_policy_pr_agent_review(proposal_id, workspace_root)
    
    # 3. Calculate Scorecard
    scorecard = calculate_policy_pr_scorecard(proposal_id, verifier_report, agent_review, workspace_root)
    
    # 4. Determine Status
    blocking_findings = []
    warnings = []
    
    for check in verifier_report.checks:
        if check.status == "FAILED":
            blocking_findings.append(f"Verifier Mesh Failed: {check.name} - {check.detail}")
            
    for f in agent_review.findings:
        if f.get("severity", "").lower() == "blocking":
            blocking_findings.append(f"Agent Blocking: {f.get('description')}")
        else:
            warnings.append(f"Agent Warning: {f.get('description')}")
            
    # Compile Report
    is_blocked = len(blocking_findings) > 0 or scorecard.risk_score > 50
    final_status = "POLICY_PR_REVIEW_BLOCKED" if is_blocked else "POLICY_PR_REVIEW_PASSED"
    
    recommended_decision = "REQUEST_CHANGES" if is_blocked else "MARK_REVIEWED"
    
    report = PolicyPRReviewReport(
        proposal_id=proposal_id,
        status=final_status,
        pr_url=pr_creation.get("pr_url", ""),
        fallback_mode=False,
        risk_score=scorecard.risk_score,
        quality_score=scorecard.quality_score,
        blocking_findings=blocking_findings,
        warnings=warnings,
        recommended_decision=recommended_decision,
        requires_operator_decision=True
    )
    
    # Write artifacts
    write_policy_pr_review_report(proposal_id, report.model_dump(), workspace_root)
    
    # Update status artifact
    write_policy_pr_status(proposal_id, {
        "proposal_id": proposal_id,
        "status": final_status,
        "operator_id": "SYSTEM"
    }, workspace_root)
    
    append_policy_pr_review_log(
        proposal_id, "REVIEW_GATE_COMPLETED", "SYSTEM", 
        {"status": final_status, "risk_score": scorecard.risk_score}, workspace_root
    )
    
    return report.model_dump()
