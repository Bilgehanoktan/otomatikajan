from __future__ import annotations

import os
from datetime import datetime
from typing import Dict, Any, Optional
from services.project_factory.models import (
    ProjectFactoryIntake,
    RequirementGate,
    ApproveScopeRequest,
    RequestRevisionRequest,
    RejectRequest
)
from services.project_factory.artifacts import (
    load_project_factory_artifacts,
    write_project_factory_artifacts
)
from services.project_factory.sandbox_scaffolder import scaffold_project_sandbox
from services.project_factory.gate_logs import record_gate_decision

def approve_project_scope(
    project_id: str,
    req: ApproveScopeRequest,
    workspace_root: Optional[str] = None
) -> Dict[str, Any]:
    """
    Resolves the Requirement Gate as APPROVED (SCOPE_APPROVED).
    Triggers safe sandbox scaffolding, updates models, saves artifacts, and logs decisions.
    """
    brief, gate = load_project_factory_artifacts(project_id, workspace_root)

    # State Machine checks: only WAITING_FOR_OPERATOR is valid for resolution
    if gate.status != "WAITING_FOR_OPERATOR":
        raise ValueError(f"Requirement Gate for project {project_id} has already been resolved with status {gate.status}")

    resolved_time = datetime.utcnow().isoformat() + "Z"

    # 1. Update Requirement Gate Model
    gate.status = "SCOPE_APPROVED"
    gate.implementation_allowed = False  # As per strict constraints
    gate.sandbox_ready = True
    gate.approved_by = req.operator_id
    gate.rationale = req.rationale
    gate.resolved_at = resolved_time
    gate.scope_adjustments = req.approved_scope

    # 2. Update Brief Model
    brief.status = "SCOPE_APPROVED"

    # 3. Scaffold sandbox
    sandbox_manifest = scaffold_project_sandbox(brief, workspace_root)

    # 4. Save updated artifacts to disk
    write_project_factory_artifacts(brief, gate, workspace_root)

    # 5. Log decision in append-only gate_decisions.jsonl
    log_details = {
        "approved_scope": req.approved_scope,
        "risk_acknowledgement": req.risk_acknowledgement,
        "sandbox_manifest": sandbox_manifest
    }
    record_gate_decision(
        project_id=project_id,
        action="APPROVE_SCOPE",
        operator_id=req.operator_id,
        rationale=req.rationale,
        details=log_details,
        workspace_root=workspace_root
    )

    return {
        "status": "success",
        "project_id": project_id,
        "gate_status": gate.status,
        "sandbox_ready": gate.sandbox_ready,
        "sandbox_manifest": sandbox_manifest
    }

def request_project_revision(
    project_id: str,
    req: RequestRevisionRequest,
    workspace_root: Optional[str] = None
) -> Dict[str, Any]:
    """
    Resolves the Requirement Gate as REVISION_REQUESTED.
    """
    brief, gate = load_project_factory_artifacts(project_id, workspace_root)

    if gate.status != "WAITING_FOR_OPERATOR":
        raise ValueError(f"Requirement Gate for project {project_id} has already been resolved with status {gate.status}")

    resolved_time = datetime.utcnow().isoformat() + "Z"

    # 1. Update Models
    gate.status = "REVISION_REQUESTED"
    gate.implementation_allowed = False
    gate.sandbox_ready = False
    gate.approved_by = req.operator_id
    gate.rationale = req.rationale
    gate.resolved_at = resolved_time
    gate.scope_adjustments = req.revision_notes

    brief.status = "REVISION_REQUESTED"

    # 2. Save updated artifacts
    write_project_factory_artifacts(brief, gate, workspace_root)

    # 3. Log decision
    log_details = {
        "revision_notes": req.revision_notes
    }
    record_gate_decision(
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
        "gate_status": gate.status,
        "sandbox_ready": gate.sandbox_ready
    }

def reject_project_intake(
    project_id: str,
    req: RejectRequest,
    workspace_root: Optional[str] = None
) -> Dict[str, Any]:
    """
    Resolves the Requirement Gate as REJECTED.
    """
    brief, gate = load_project_factory_artifacts(project_id, workspace_root)

    if gate.status != "WAITING_FOR_OPERATOR":
        raise ValueError(f"Requirement Gate for project {project_id} has already been resolved with status {gate.status}")

    resolved_time = datetime.utcnow().isoformat() + "Z"

    # 1. Update Models
    gate.status = "REJECTED"
    gate.implementation_allowed = False
    gate.sandbox_ready = False
    gate.approved_by = req.operator_id
    gate.rationale = req.rationale
    gate.resolved_at = resolved_time

    brief.status = "REJECTED"

    # 2. Save updated artifacts
    write_project_factory_artifacts(brief, gate, workspace_root)

    # 3. Log decision
    record_gate_decision(
        project_id=project_id,
        action="REJECT",
        operator_id=req.operator_id,
        rationale=req.rationale,
        workspace_root=workspace_root
    )

    return {
        "status": "success",
        "project_id": project_id,
        "gate_status": gate.status,
        "sandbox_ready": gate.sandbox_ready
    }
