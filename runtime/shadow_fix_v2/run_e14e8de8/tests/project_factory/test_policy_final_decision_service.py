import pytest
import os
import json
from services.project_factory.models import PolicyFinalDecisionRequest, PolicyFinalRevisionRequest
from services.project_factory.policy_final_decision_service import (
    execute_final_approve,
    execute_final_reject,
    execute_final_revision_request
)
from services.project_factory.artifacts import _resolve_policy_autopilot_dir

@pytest.fixture
def workspace_with_ready_state(tmp_path):
    workspace = tmp_path
    autopilot_dir = _resolve_policy_autopilot_dir(str(workspace))
    autopilot_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Status is READY
    (autopilot_dir / "policy_pr_status.json").write_text(json.dumps({
        "status": "POLICY_READY_FOR_FINAL_DECISION"
    }))
    
    # 2. PR Review is PASSED
    (autopilot_dir / "policy_pr_review_report.json").write_text(json.dumps({
        "status": "POLICY_PR_REVIEW_PASSED",
        "blocking_findings": []
    }))
    
    # 3. Verifier Mesh is PASSED
    (autopilot_dir / "policy_verifier_mesh_report.json").write_text(json.dumps({
        "status": "PASSED"
    }))
    
    # 4. Safe PR creation
    (autopilot_dir / "policy_pr_creation.json").write_text(json.dumps({
        "merge_performed": False,
        "force_push_performed": False,
        "production_direct_write": False
    }))
    
    # 5. Safe Apply preview
    (autopilot_dir / "policy_apply_preview.json").write_text(json.dumps({
        "production_apply_performed": False,
        "policy_files_modified": False
    }))
    
    return str(workspace)

def test_final_approve_success(workspace_with_ready_state):
    req = PolicyFinalDecisionRequest(
        operator_id="test-op",
        rationale="Looks good",
        risk_acknowledgement=True
    )
    result = execute_final_approve("POL-01", req, workspace_with_ready_state)
    
    assert result["status"] == "success"
    assert result["new_status"] == "POLICY_LIFECYCLE_CLOSED"
    assert "release_id" in result
    
    autopilot_dir = _resolve_policy_autopilot_dir(workspace_with_ready_state)
    assert (autopilot_dir / "policy_final_decision_logs.jsonl").exists()

def test_final_approve_fails_without_risk_ack(workspace_with_ready_state):
    req = PolicyFinalDecisionRequest(
        operator_id="test-op",
        rationale="Looks good",
        risk_acknowledgement=False
    )
    with pytest.raises(ValueError, match="Risk acknowledgement is required"):
        execute_final_approve("POL-01", req, workspace_with_ready_state)

def test_final_approve_fails_on_blocking_findings(workspace_with_ready_state):
    autopilot_dir = _resolve_policy_autopilot_dir(workspace_with_ready_state)
    (autopilot_dir / "policy_pr_review_report.json").write_text(json.dumps({
        "status": "POLICY_PR_REVIEW_PASSED",
        "blocking_findings": ["Some issue"]
    }))
    
    req = PolicyFinalDecisionRequest(
        operator_id="test-op",
        rationale="Looks good",
        risk_acknowledgement=True
    )
    with pytest.raises(ValueError, match="blocking findings"):
        execute_final_approve("POL-01", req, workspace_with_ready_state)

def test_final_approve_fails_on_merge_performed(workspace_with_ready_state):
    autopilot_dir = _resolve_policy_autopilot_dir(workspace_with_ready_state)
    (autopilot_dir / "policy_pr_creation.json").write_text(json.dumps({
        "merge_performed": True,
        "force_push_performed": False,
        "production_direct_write": False
    }))
    
    req = PolicyFinalDecisionRequest(
        operator_id="test-op",
        rationale="Looks good",
        risk_acknowledgement=True
    )
    with pytest.raises(ValueError, match="merge_performed is True"):
        execute_final_approve("POL-01", req, workspace_with_ready_state)

def test_final_reject(workspace_with_ready_state):
    req = PolicyFinalDecisionRequest(
        operator_id="test-op",
        rationale="Rejecting this",
        risk_acknowledgement=True
    )
    result = execute_final_reject("POL-01", req, workspace_with_ready_state)
    
    assert result["status"] == "success"
    assert result["new_status"] == "FINAL_POLICY_REJECTED"

def test_final_revision_request(workspace_with_ready_state):
    req = PolicyFinalRevisionRequest(
        operator_id="test-op",
        rationale="Needs more work",
        revision_notes="Please update X and Y"
    )
    result = execute_final_revision_request("POL-01", req, workspace_with_ready_state)
    
    assert result["status"] == "success"
    assert result["new_status"] == "FINAL_POLICY_REVISION_REQUESTED"
