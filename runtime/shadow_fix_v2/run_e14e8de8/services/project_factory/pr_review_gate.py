"""
PR Review Gate — main orchestrator for Phase 11.

Coordinates:
  1. PR-Agent static review
  2. Verifier Mesh checks
  3. Scorecard computation
  4. Review report generation
  5. State transitions

Handles both draft PR and local candidate fallback scenarios.
"""
from __future__ import annotations

from typing import Optional
from services.project_factory.models import (
    PrReviewRunRequest,
    PrReviewReport,
)
from services.project_factory.artifacts import (
    load_project_factory_artifacts,
    write_project_factory_artifacts,
    load_draft_pr_creation,
    write_pr_review_report,
)
from services.project_factory.pr_agent_review import run_pr_agent_review
from services.project_factory.verifier_mesh_adapter import run_verifier_mesh
from services.project_factory.pr_review_scorecard import compute_pr_review_scorecard
from services.project_factory.pr_review_logs import record_pr_review_decision

REVIEWABLE_STATES = {
    "PR_CREATED_WAITING_REVIEW",
    "PR_CREATION_BLOCKED",
    "PR_REVIEW_REQUEST_CHANGES",
    "PR_REVIEW_DEFERRED",
}


def run_pr_review_gate(
    project_id: str,
    req: PrReviewRunRequest,
    workspace_root: Optional[str] = None,
) -> PrReviewReport:
    """
    Executes the full PR Review Gate pipeline.
    """
    if not req.risk_acknowledgement:
        raise ValueError("Operator must acknowledge risks (risk_acknowledgement=true).")

    # 1. Validate current state
    brief, gate = load_project_factory_artifacts(project_id, workspace_root)
    if gate.status not in REVIEWABLE_STATES:
        raise ValueError(
            f"Cannot run PR review from state '{gate.status}'. "
            f"Must be one of {REVIEWABLE_STATES}"
        )

    # 2. Transition to RUNNING
    brief.status = "PR_REVIEW_RUNNING"
    gate.status = "PR_REVIEW_RUNNING"
    write_project_factory_artifacts(brief, gate, workspace_root)

    record_pr_review_decision(
        project_id=project_id,
        action="PR_REVIEW_STARTED",
        operator_id=req.operator_id,
        rationale=req.rationale,
        workspace_root=workspace_root,
    )

    # 3. Determine review mode (draft PR vs local candidate fallback)
    pr_creation = load_draft_pr_creation(project_id, workspace_root)
    pr_url = ""
    fallback_mode = False

    if pr_creation and pr_creation.get("pr_url"):
        pr_url = pr_creation["pr_url"]
    else:
        fallback_mode = True

    try:
        # 4. Run PR-Agent static review
        pr_agent_result = run_pr_agent_review(project_id, workspace_root)

        # 5. Run Verifier Mesh
        verifier_result = run_verifier_mesh(project_id, workspace_root)

        # 6. Compute scorecard
        scorecard = compute_pr_review_scorecard(
            project_id, pr_agent_result, verifier_result, workspace_root
        )

        # 7. Determine review status
        blocking_findings = [
            f.description for f in pr_agent_result.findings if f.severity == "blocking"
        ]
        warnings = [
            f.description for f in pr_agent_result.findings if f.severity == "warning"
        ]

        # Verifier failures are also blocking
        for check in verifier_result.checks:
            if check.status == "FAILED":
                blocking_findings.append(f"Verifier '{check.name}' FAILED: {check.detail}")

        if len(blocking_findings) > 0:
            review_status = "PR_REVIEW_BLOCKED"
            recommended = "BLOCK"
        elif len(warnings) > 0:
            review_status = "PR_REVIEW_PASSED"
            recommended = "REQUEST_CHANGES"
        else:
            review_status = "PR_REVIEW_PASSED"
            recommended = "MARK_REVIEWED"

        report = PrReviewReport(
            project_id=project_id,
            status=review_status,
            review_mode=req.review_mode,
            pr_url=pr_url,
            fallback_mode=fallback_mode,
            risk_score=scorecard.risk_score,
            quality_score=scorecard.quality_score,
            blocking_findings=blocking_findings,
            warnings=warnings,
            recommended_decision=recommended,
            requires_operator_decision=True,
        )

    except Exception as e:
        report = PrReviewReport(
            project_id=project_id,
            status="PR_REVIEW_BLOCKED",
            review_mode=req.review_mode,
            pr_url=pr_url,
            fallback_mode=fallback_mode,
            blocking_findings=[f"Review pipeline error: {e}"],
            recommended_decision="BLOCK",
            requires_operator_decision=True,
        )

    # 8. Persist report
    write_pr_review_report(project_id, report.model_dump(), workspace_root)

    # 9. Update state
    brief.status = report.status
    gate.status = report.status
    write_project_factory_artifacts(brief, gate, workspace_root)

    record_pr_review_decision(
        project_id=project_id,
        action="PR_REVIEW_COMPLETED",
        operator_id=req.operator_id,
        rationale=f"Review completed: {report.status}",
        details={"status": report.status, "risk_score": report.risk_score, "quality_score": report.quality_score},
        workspace_root=workspace_root,
    )

    return report
