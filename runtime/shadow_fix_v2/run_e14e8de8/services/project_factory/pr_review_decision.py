"""
PR Review Decision Handler.

Processes operator decisions on the PR Review Gate:
  - REQUEST_CHANGES → PR_REVIEW_REQUEST_CHANGES
  - MARK_REVIEWED   → READY_FOR_FINAL_OPERATOR_DECISION
  - BLOCK           → PR_REVIEW_BLOCKED
  - DEFER           → PR_REVIEW_DEFERRED
"""
from __future__ import annotations

from typing import Optional
from services.project_factory.models import PrReviewDecisionRequest
from services.project_factory.artifacts import (
    load_project_factory_artifacts,
    write_project_factory_artifacts,
    load_pr_review_report,
    write_pr_review_report,
)
from services.project_factory.pr_review_logs import record_pr_review_decision

VALID_DECISIONS = {"REQUEST_CHANGES", "MARK_REVIEWED", "BLOCK", "DEFER"}

DECISION_STATUS_MAP = {
    "REQUEST_CHANGES": "PR_REVIEW_REQUEST_CHANGES",
    "MARK_REVIEWED": "READY_FOR_FINAL_OPERATOR_DECISION",
    "BLOCK": "PR_REVIEW_BLOCKED",
    "DEFER": "PR_REVIEW_DEFERRED",
}

DECIDABLE_STATES = {
    "PR_REVIEW_PASSED",
    "PR_REVIEW_BLOCKED",
    "PR_REVIEW_REQUEST_CHANGES",
    "PR_REVIEW_DEFERRED",
}


def apply_pr_review_decision(
    project_id: str,
    req: PrReviewDecisionRequest,
    workspace_root: Optional[str] = None,
) -> dict:
    """
    Applies an operator decision to the PR Review Gate.
    """
    if req.decision not in VALID_DECISIONS:
        raise ValueError(f"Invalid decision '{req.decision}'. Must be one of {VALID_DECISIONS}")

    if not req.risk_acknowledgement:
        raise ValueError("Operator must acknowledge risks (risk_acknowledgement=true).")

    # 1. Load current state
    brief, gate = load_project_factory_artifacts(project_id, workspace_root)

    if gate.status not in DECIDABLE_STATES:
        raise ValueError(
            f"Cannot apply decision from state '{gate.status}'. "
            f"Must be one of {DECIDABLE_STATES}"
        )

    # 2. Compute new status
    new_status = DECISION_STATUS_MAP[req.decision]

    # 3. Update state
    brief.status = new_status
    gate.status = new_status
    write_project_factory_artifacts(brief, gate, workspace_root)

    # 4. Update pr_review_report status
    report_data = load_pr_review_report(project_id, workspace_root)
    if report_data:
        report_data["status"] = new_status
        write_pr_review_report(project_id, report_data, workspace_root)

    # 5. Log
    record_pr_review_decision(
        project_id=project_id,
        action=f"DECISION_{req.decision}",
        operator_id=req.operator_id,
        rationale=req.rationale,
        details={"decision": req.decision, "new_status": new_status},
        workspace_root=workspace_root,
    )

    return {
        "project_id": project_id,
        "decision": req.decision,
        "new_status": new_status,
        "operator_id": req.operator_id,
    }
