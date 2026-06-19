"""
Final Decision Service — main orchestrator for Phase 12.

Handles:
  - FINAL_APPROVED: safety validation → release archive → PROJECT_CLOSED
  - FINAL_REJECTED: state transition + log
  - FINAL_REVISION_REQUESTED: state transition + log
"""
from __future__ import annotations

from typing import Optional, Dict, Any, List
from services.project_factory.models import (
    FinalApproveRequest,
    FinalRejectRequest,
    FinalRevisionRequest,
    FinalOperatorDecision,
    ReleaseManifest,
)
from services.project_factory.artifacts import (
    load_project_factory_artifacts,
    write_project_factory_artifacts,
    write_final_operator_decision,
    load_draft_pr_creation,
    _load_json_artifact,
)
from services.project_factory.release_archiver import build_release_archive
from services.project_factory.final_decision_logs import record_final_decision

FINAL_DECIDABLE_STATES = {"READY_FOR_FINAL_OPERATOR_DECISION"}

# Safety flags that must be false for final approve
SAFETY_CHECKS = [
    ("delivery_manifest.json", "production_apply_allowed", False),
    ("apply_preview.json", "production_apply_performed", False),
    ("draft_pr_plan.json", "git_operations_performed", False),
]

PR_CREATION_SAFETY_CHECKS = [
    ("merge_performed", False),
    ("force_push_performed", False),
    ("production_direct_write", False),
]


def _validate_safety_for_approve(
    project_id: str,
    workspace_root: Optional[str] = None,
) -> List[str]:
    """
    Returns list of safety violation messages. Empty list = safe.
    """
    violations: List[str] = []

    # Check artifact-level safety flags
    for filename, key, expected in SAFETY_CHECKS:
        data = _load_json_artifact(project_id, filename, workspace_root)
        if data is not None:
            actual = data.get(key)
            if actual != expected:
                violations.append(f"{filename}.{key} is {actual}, expected {expected}")

    # Check PR creation flags (optional — may not exist in fallback mode)
    pr_creation = load_draft_pr_creation(project_id, workspace_root)
    if pr_creation:
        for key, expected in PR_CREATION_SAFETY_CHECKS:
            actual = pr_creation.get(key)
            if actual != expected:
                violations.append(f"draft_pr_creation.{key} is {actual}, expected {expected}")

    # Check PR review report
    pr_review = _load_json_artifact(project_id, "pr_review_report.json", workspace_root)
    if pr_review:
        if pr_review.get("status") not in ("PR_REVIEW_PASSED",):
            violations.append(f"pr_review_report.status is {pr_review.get('status')}, expected PR_REVIEW_PASSED")
        blocking = pr_review.get("blocking_findings", [])
        if blocking:
            violations.append(f"pr_review_report has {len(blocking)} blocking finding(s)")

    # Check verifier mesh
    verifier = _load_json_artifact(project_id, "verifier_mesh_report.json", workspace_root)
    if verifier:
        if verifier.get("status") != "PASSED":
            violations.append(f"verifier_mesh_report.status is {verifier.get('status')}, expected PASSED")

    return violations


def final_approve(
    project_id: str,
    req: FinalApproveRequest,
    workspace_root: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Executes the final approve flow: validate → archive → close.
    """
    if not req.risk_acknowledgement:
        raise ValueError("Operator must acknowledge risks (risk_acknowledgement=true).")

    # 1. Validate current state
    brief, gate = load_project_factory_artifacts(project_id, workspace_root)
    if gate.status not in FINAL_DECIDABLE_STATES:
        raise ValueError(
            f"Cannot final approve from state '{gate.status}'. "
            f"Must be one of {FINAL_DECIDABLE_STATES}"
        )

    # 2. Run safety validation
    violations = _validate_safety_for_approve(project_id, workspace_root)
    if violations:
        raise ValueError(f"Safety validation failed: {'; '.join(violations)}")

    # 3. Create final decision
    release_id = f"REL-{project_id}"
    decision = FinalOperatorDecision(
        project_id=project_id,
        decision="FINAL_APPROVED",
        operator_id=req.operator_id,
        rationale=req.rationale,
        risk_acknowledgement=True,
        release_id=release_id,
    )
    write_final_operator_decision(project_id, decision.model_dump(), workspace_root)

    # 4. Build release archive
    manifest = build_release_archive(
        project_id=project_id,
        release_id=release_id,
        operator_id=req.operator_id,
        rationale=req.rationale,
        workspace_root=workspace_root,
    )

    # 5. Transition to PROJECT_CLOSED
    brief.status = "PROJECT_CLOSED"
    gate.status = "PROJECT_CLOSED"
    write_project_factory_artifacts(brief, gate, workspace_root)

    # 6. Log
    record_final_decision(
        project_id=project_id,
        action="FINAL_APPROVE",
        operator_id=req.operator_id,
        rationale=req.rationale,
        from_status="READY_FOR_FINAL_OPERATOR_DECISION",
        to_status="PROJECT_CLOSED",
        details={"release_id": release_id, "evidence_count": manifest.evidence_count},
        workspace_root=workspace_root,
    )

    return {
        "decision": decision.model_dump(),
        "release_manifest": manifest.model_dump(),
        "status": "PROJECT_CLOSED",
    }


def final_reject(
    project_id: str,
    req: FinalRejectRequest,
    workspace_root: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Rejects the project at final decision stage.
    """
    brief, gate = load_project_factory_artifacts(project_id, workspace_root)
    if gate.status not in FINAL_DECIDABLE_STATES:
        raise ValueError(
            f"Cannot final reject from state '{gate.status}'. "
            f"Must be one of {FINAL_DECIDABLE_STATES}"
        )

    decision = FinalOperatorDecision(
        project_id=project_id,
        decision="FINAL_REJECTED",
        operator_id=req.operator_id,
        rationale=req.rationale,
    )
    write_final_operator_decision(project_id, decision.model_dump(), workspace_root)

    brief.status = "FINAL_REJECTED"
    gate.status = "FINAL_REJECTED"
    write_project_factory_artifacts(brief, gate, workspace_root)

    record_final_decision(
        project_id=project_id,
        action="FINAL_REJECT",
        operator_id=req.operator_id,
        rationale=req.rationale,
        from_status="READY_FOR_FINAL_OPERATOR_DECISION",
        to_status="FINAL_REJECTED",
        workspace_root=workspace_root,
    )

    return {"decision": decision.model_dump(), "status": "FINAL_REJECTED"}


def final_request_revision(
    project_id: str,
    req: FinalRevisionRequest,
    workspace_root: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Requests a revision before final approval.
    """
    brief, gate = load_project_factory_artifacts(project_id, workspace_root)
    if gate.status not in FINAL_DECIDABLE_STATES:
        raise ValueError(
            f"Cannot request revision from state '{gate.status}'. "
            f"Must be one of {FINAL_DECIDABLE_STATES}"
        )

    decision = FinalOperatorDecision(
        project_id=project_id,
        decision="FINAL_REVISION_REQUESTED",
        operator_id=req.operator_id,
        rationale=req.rationale,
        revision_notes=req.revision_notes,
    )
    write_final_operator_decision(project_id, decision.model_dump(), workspace_root)

    brief.status = "FINAL_REVISION_REQUESTED"
    gate.status = "FINAL_REVISION_REQUESTED"
    write_project_factory_artifacts(brief, gate, workspace_root)

    record_final_decision(
        project_id=project_id,
        action="FINAL_REVISION_REQUESTED",
        operator_id=req.operator_id,
        rationale=req.rationale,
        from_status="READY_FOR_FINAL_OPERATOR_DECISION",
        to_status="FINAL_REVISION_REQUESTED",
        details={"revision_notes": req.revision_notes},
        workspace_root=workspace_root,
    )

    return {"decision": decision.model_dump(), "status": "FINAL_REVISION_REQUESTED"}
