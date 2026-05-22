from services.project_factory.models import PolicyPRReviewScorecard, PolicyVerifierMeshReport, PolicyPRAgentReview
from services.project_factory.artifacts import write_policy_pr_review_scorecard

def calculate_policy_pr_scorecard(
    proposal_id: str,
    verifier_report: PolicyVerifierMeshReport,
    agent_review: PolicyPRAgentReview,
    workspace_root: str = None
) -> PolicyPRReviewScorecard:
    """
    Calculates risk and quality scores based on the review checks and static analysis.
    """
    risk_score = 0
    quality_score = 100
    
    # 1. Verifier checks
    failed_checks = [c for c in verifier_report.checks if c.status == "FAILED"]
    total_checks = len(verifier_report.checks)
    verifier_pass_rate = 1.0
    if total_checks > 0:
        verifier_pass_rate = (total_checks - len(failed_checks)) / total_checks
        
    risk_score += len(failed_checks) * 30  # High penalty for failing safety checks
    
    # 2. Agent findings
    blocking_count = 0
    warning_count = 0
    
    for f in agent_review.findings:
        sev = f.get("severity", "").lower()
        if sev == "blocking":
            blocking_count += 1
            risk_score += 20
            quality_score -= 15
        elif sev == "warning":
            warning_count += 1
            risk_score += 5
            quality_score -= 5
            
    # Cap scores
    risk_score = min(max(risk_score, 0), 100)
    quality_score = min(max(quality_score, 0), 100)
    
    scorecard = PolicyPRReviewScorecard(
        risk_score=risk_score,
        quality_score=quality_score,
        blocking_count=blocking_count,
        warning_count=warning_count,
        verifier_pass_rate=verifier_pass_rate
    )
    
    write_policy_pr_review_scorecard(scorecard.model_dump(), workspace_root)
    return scorecard
