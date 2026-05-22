"""
PR Review Scorecard.

Computes a composite risk_score and quality_score from
PR-Agent review findings and Verifier Mesh check results.
"""
from __future__ import annotations

from typing import Optional
from services.project_factory.artifacts import write_pr_review_scorecard
from services.project_factory.models import (
    PrAgentReview,
    VerifierMeshReport,
    PrReviewScorecard,
)


def compute_pr_review_scorecard(
    project_id: str,
    pr_agent: PrAgentReview,
    verifier: VerifierMeshReport,
    workspace_root: Optional[str] = None,
) -> PrReviewScorecard:
    """
    Aggregates PR-Agent review and Verifier Mesh results into a scorecard.
    """
    blocking_count = sum(1 for f in pr_agent.findings if f.severity == "blocking")
    warning_count = sum(1 for f in pr_agent.findings if f.severity == "warning")

    # Risk score: 0–100, higher = more risky
    risk_score = min(100, blocking_count * 30 + warning_count * 10)

    # Verifier pass rate
    total_checks = len(verifier.checks)
    passed_checks = sum(1 for c in verifier.checks if c.status == "PASSED")
    verifier_pass_rate = (passed_checks / total_checks) if total_checks > 0 else 1.0

    # Failed verifier checks increase risk
    failed_verifiers = sum(1 for c in verifier.checks if c.status == "FAILED")
    risk_score = min(100, risk_score + failed_verifiers * 25)

    # Quality score: inverse of risk with verifier bonus
    quality_score = max(0, int(100 - risk_score * 0.8 - (1.0 - verifier_pass_rate) * 20))

    scorecard = PrReviewScorecard(
        risk_score=risk_score,
        quality_score=quality_score,
        blocking_count=blocking_count,
        warning_count=warning_count,
        verifier_pass_rate=round(verifier_pass_rate, 2),
    )

    write_pr_review_scorecard(project_id, scorecard.model_dump(), workspace_root)
    return scorecard
