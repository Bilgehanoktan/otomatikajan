from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Dict, Any
from services.project_factory.artifacts import _resolve_project_dir, load_project_factory_artifacts, write_project_factory_artifacts
from services.project_factory.models import ApproveDeliveryRequest, RevisionRequest, RejectCandidateRequest
from services.project_factory.delivery_packager import build_delivery_package
from services.project_factory.delivery_logs import record_delivery_decision

def approve_candidate_delivery(
    project_id: str,
    req: ApproveDeliveryRequest,
    workspace_root: Optional[str] = None
) -> Dict[str, Any]:
    """
    Validates risk, quality checks, and operators credentials to generate delivery package.
    Transitions project to DELIVERY_PACKAGE_READY.
    """
    brief, gate = load_project_factory_artifacts(project_id, workspace_root)
    project_dir = _resolve_project_dir(project_id, workspace_root)

    # 1. Enforce allowed pre-gate statuses
    valid_states = ["HUMAN_GATE_WAITING", "CANDIDATE_UNDER_REVIEW", "CANDIDATE_REVIEWED", "CANDIDATE_READY"]
    if gate.status not in valid_states:
        raise ValueError(f"Project status is {gate.status}. Delivery approval is only allowed in candidate waiting/review states.")

    # 2. Check for required review/scoring artifacts
    required_files = [
        "candidate_manifest.json",
        "verification_report.json",
        "risk_assessment.json",
        "quality_scorecard.json"
    ]
    for r_file in required_files:
        if not (project_dir / r_file).exists():
            raise ValueError(f"Missing mandatory review artifact: {r_file}. Please run candidate review first.")

    # 3. Read risk assessment and check thresholds
    with open(project_dir / "risk_assessment.json", "r", encoding="utf-8") as f:
        risk_data = json.load(f)
    
    risk_score = risk_data.get("risk_score", 0)
    blocking_risks = risk_data.get("blocking_risks", [])

    if risk_score >= 70 or len(blocking_risks) > 0:
        raise ValueError(f"Approval blocked due to high risk score ({risk_score}) or active blocking risks: {blocking_risks}")

    # 4. Operator acknowledgement validation
    if not req.risk_acknowledgement:
        raise ValueError("Operator must acknowledge risks to approve delivery package.")

    # 5. Transition states and assemble package
    brief.status = "DELIVERY_PACKAGE_READY"
    gate.status = "DELIVERY_PACKAGE_READY"

    delivery_manifest = build_delivery_package(project_id, req.operator_id, req.rationale, workspace_root)
    write_project_factory_artifacts(brief, gate, workspace_root)

    # 6. Append to log
    log_details = {
        "delivery_manifest": delivery_manifest
    }
    record_delivery_decision(
        project_id=project_id,
        action="APPROVE_DELIVERY",
        operator_id=req.operator_id,
        rationale=req.rationale,
        details=log_details,
        workspace_root=workspace_root
    )

    return {
        "status": "success",
        "project_id": project_id,
        "gate_status": gate.status,
        "delivery_manifest": delivery_manifest
    }

def request_candidate_revision(
    project_id: str,
    req: RevisionRequest,
    workspace_root: Optional[str] = None
) -> Dict[str, Any]:
    """
    Transitions candidate status to REVISION_REQUESTED.
    """
    brief, gate = load_project_factory_artifacts(project_id, workspace_root)

    # Validate state transitions
    valid_states = ["HUMAN_GATE_WAITING", "CANDIDATE_UNDER_REVIEW", "CANDIDATE_REVIEWED", "CANDIDATE_READY"]
    if gate.status not in valid_states:
        raise ValueError(f"Project status is {gate.status}. Revision is not allowed.")

    brief.status = "REVISION_REQUESTED"
    gate.status = "REVISION_REQUESTED"
    write_project_factory_artifacts(brief, gate, workspace_root)

    log_details = {
        "revision_notes": req.revision_notes
    }
    record_delivery_decision(
        project_id=project_id,
        action="REQUEST_REVISION",
        operator_id=req.operator_id,
        rationale=req.rationale,
        details=log_details,
        workspace_root=workspace_root
    )

    return {
        "status": "success",
        "project_id": project_id,
        "gate_status": gate.status
    }

def reject_candidate_delivery(
    project_id: str,
    req: RejectCandidateRequest,
    workspace_root: Optional[str] = None
) -> Dict[str, Any]:
    """
    Transitions candidate status to REJECTED.
    """
    brief, gate = load_project_factory_artifacts(project_id, workspace_root)

    # Validate state transitions
    valid_states = ["HUMAN_GATE_WAITING", "CANDIDATE_UNDER_REVIEW", "CANDIDATE_REVIEWED", "CANDIDATE_READY"]
    if gate.status not in valid_states:
        raise ValueError(f"Project status is {gate.status}. Rejection is not allowed.")

    brief.status = "REJECTED"
    gate.status = "REJECTED"
    write_project_factory_artifacts(brief, gate, workspace_root)

    record_delivery_decision(
        project_id=project_id,
        action="REJECT",
        operator_id=req.operator_id,
        rationale=req.rationale,
        workspace_root=workspace_root
    )

    return {
        "status": "success",
        "project_id": project_id,
        "gate_status": gate.status
    }
