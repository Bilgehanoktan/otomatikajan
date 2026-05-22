from typing import Optional, Dict, Any
import json
from services.project_factory.models import PolicyFinalDecisionRequest, PolicyFinalRevisionRequest
from services.project_factory.artifacts import (
    _resolve_policy_autopilot_dir, 
    load_policy_pr_status, 
    write_policy_pr_status,
    load_policy_pr_review_report,
    load_policy_verifier_mesh_report,
    load_policy_pr_creation,
    load_policy_draft_pr_plan,
    load_policy_apply_preview
)
from services.project_factory.policy_final_decision_logs import append_policy_final_decision_log
from services.project_factory.policy_release_archiver import create_policy_release_archive

def validate_final_approve_security(proposal_id: str, workspace_root: Optional[str] = None):
    """
    Validates that no unsafe operations were performed before allowing a final approve.
    """
    # 1. Review status MUST be PASSED
    review_report = load_policy_pr_review_report(workspace_root)
    if not review_report or review_report.get("status") != "POLICY_PR_REVIEW_PASSED":
        raise ValueError("Cannot final approve: PR Review status is not PASSED.")
    if review_report.get("blocking_findings"):
        raise ValueError("Cannot final approve: PR Review has blocking findings.")
        
    # 2. Verifier Mesh MUST be PASSED
    mesh = load_policy_verifier_mesh_report(workspace_root)
    if not mesh or mesh.get("status") != "PASSED":
        raise ValueError("Cannot final approve: Verifier Mesh is not PASSED.")
        
    # 3. Check for specific safety flags across artifacts
    creation = load_policy_pr_creation(workspace_root)
    if creation:
        if creation.get("merge_performed"):
            raise ValueError("Safety violation: merge_performed is True.")
        if creation.get("force_push_performed"):
            raise ValueError("Safety violation: force_push_performed is True.")
        if creation.get("production_direct_write"):
            raise ValueError("Safety violation: production_direct_write is True.")
            
    pr_plan = load_policy_draft_pr_plan(workspace_root)
    if pr_plan:
        if pr_plan.get("git_operations_performed"):
            raise ValueError("Safety violation: pr plan performed git operations prematurely.")
            
    apply_preview = load_policy_apply_preview(workspace_root)
    if apply_preview:
        if apply_preview.get("production_apply_performed"):
            raise ValueError("Safety violation: production_apply_performed is True.")
        if apply_preview.get("policy_files_modified"):
            raise ValueError("Safety violation: policy_files_modified is True.")

def execute_final_approve(proposal_id: str, request: PolicyFinalDecisionRequest, workspace_root: Optional[str] = None) -> Dict[str, Any]:
    """
    Approves the policy proposal and closes the lifecycle by creating the release archive.
    """
    if not request.risk_acknowledgement:
        raise ValueError("Risk acknowledgement is required to final approve the policy.")
        
    status_data = load_policy_pr_status(workspace_root)
    if not status_data or status_data.get("status") != "POLICY_READY_FOR_FINAL_DECISION":
        raise ValueError(f"Proposal must be in POLICY_READY_FOR_FINAL_DECISION status. Current: {status_data.get('status') if status_data else 'None'}")
        
    validate_final_approve_security(proposal_id, workspace_root)
    
    # Generate the release archive
    manifest = create_policy_release_archive(proposal_id, request.operator_id, "FINAL_POLICY_APPROVED", workspace_root)
    
    # Append log
    append_policy_final_decision_log({
        "proposal_id": proposal_id,
        "action": "FINAL_POLICY_APPROVE",
        "from_status": "POLICY_READY_FOR_FINAL_DECISION",
        "to_status": "POLICY_LIFECYCLE_CLOSED",
        "operator_id": request.operator_id,
        "rationale": request.rationale,
        "risk_acknowledgement": request.risk_acknowledgement,
        "release_id": manifest.release_id
    }, workspace_root)
    
    # Update status
    status_data["status"] = "POLICY_LIFECYCLE_CLOSED"
    write_policy_pr_status(status_data, workspace_root)
    
    return {
        "status": "success",
        "new_status": "POLICY_LIFECYCLE_CLOSED",
        "release_id": manifest.release_id,
        "evidence_count": manifest.evidence_count
    }

def execute_final_reject(proposal_id: str, request: PolicyFinalDecisionRequest, workspace_root: Optional[str] = None) -> Dict[str, Any]:
    status_data = load_policy_pr_status(workspace_root)
    if not status_data or status_data.get("status") != "POLICY_READY_FOR_FINAL_DECISION":
        raise ValueError("Proposal must be in POLICY_READY_FOR_FINAL_DECISION status.")
        
    append_policy_final_decision_log({
        "proposal_id": proposal_id,
        "action": "FINAL_POLICY_REJECT",
        "from_status": "POLICY_READY_FOR_FINAL_DECISION",
        "to_status": "FINAL_POLICY_REJECTED",
        "operator_id": request.operator_id,
        "rationale": request.rationale,
        "risk_acknowledgement": request.risk_acknowledgement
    }, workspace_root)
    
    status_data["status"] = "FINAL_POLICY_REJECTED"
    write_policy_pr_status(status_data, workspace_root)
    
    return {"status": "success", "new_status": "FINAL_POLICY_REJECTED"}

def execute_final_revision_request(proposal_id: str, request: PolicyFinalRevisionRequest, workspace_root: Optional[str] = None) -> Dict[str, Any]:
    status_data = load_policy_pr_status(workspace_root)
    if not status_data or status_data.get("status") != "POLICY_READY_FOR_FINAL_DECISION":
        raise ValueError("Proposal must be in POLICY_READY_FOR_FINAL_DECISION status.")
        
    append_policy_final_decision_log({
        "proposal_id": proposal_id,
        "action": "FINAL_POLICY_REQUEST_REVISION",
        "from_status": "POLICY_READY_FOR_FINAL_DECISION",
        "to_status": "FINAL_POLICY_REVISION_REQUESTED",
        "operator_id": request.operator_id,
        "rationale": request.rationale,
        "revision_notes": request.revision_notes,
        "risk_acknowledgement": False
    }, workspace_root)
    
    status_data["status"] = "FINAL_POLICY_REVISION_REQUESTED"
    write_policy_pr_status(status_data, workspace_root)
    
    return {"status": "success", "new_status": "FINAL_POLICY_REVISION_REQUESTED"}
