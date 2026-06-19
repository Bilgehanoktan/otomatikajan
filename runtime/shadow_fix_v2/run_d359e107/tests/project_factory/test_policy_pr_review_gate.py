import pytest
import os
import json
import tempfile
from services.project_factory.models import PolicyPRReviewRunRequest
from services.project_factory.policy_pr_review_gate import run_policy_pr_review_gate
from services.project_factory.artifacts import _resolve_policy_autopilot_dir

@pytest.fixture
def workspace_dir():
    with tempfile.TemporaryDirectory() as temp_dir:
        p_dir = _resolve_policy_autopilot_dir(temp_dir)
        p_dir.mkdir(parents=True, exist_ok=True)
        yield temp_dir

def test_run_policy_pr_review_gate_success(workspace_dir):
    p_dir = _resolve_policy_autopilot_dir(workspace_dir)
    proposal_id = "POL-1"
    
    # Write pre-requisites
    with open(p_dir / "policy_pr_creation.json", "w", encoding="utf-8") as f:
        json.dump({
            "proposal_id": proposal_id,
            "status": "POLICY_DRAFT_PR_CREATED",
            "merge_performed": False,
            "force_push_performed": False,
            "production_direct_write": False,
            "is_draft": True,
            "branch_name": "codex/policy-update",
            "modified_files": ["agents/policy.json"],
            "pr_url": "https://github.com/test/pull/1"
        }, f)
        
    with open(p_dir / "policy_apply_preview.json", "w", encoding="utf-8") as f:
        json.dump({"production_apply_performed": False}, f)
        
    with open(p_dir / "policy_draft_pr_plan.json", "w", encoding="utf-8") as f:
        json.dump({"git_operations_performed": False, "files_to_apply": ["agents/policy.json"]}, f)
        
    request = PolicyPRReviewRunRequest(
        operator_id="ADMIN",
        rationale="Running tests",
        risk_acknowledgement=True
    )
    
    report_dict = run_policy_pr_review_gate(proposal_id, request, workspace_dir)
    
    assert report_dict["status"] == "POLICY_PR_REVIEW_PASSED"
    assert report_dict["recommended_decision"] == "MARK_REVIEWED"
    
    # Check that status file is updated
    with open(p_dir / "policy_pr_status.json", "r", encoding="utf-8") as f:
        status_data = json.load(f)
        assert status_data["status"] == "POLICY_PR_REVIEW_PASSED"

def test_run_policy_pr_review_gate_blocked_by_verifier(workspace_dir):
    p_dir = _resolve_policy_autopilot_dir(workspace_dir)
    proposal_id = "POL-1"
    
    # Write pre-requisites with a failure (merge_performed = True)
    with open(p_dir / "policy_pr_creation.json", "w", encoding="utf-8") as f:
        json.dump({
            "proposal_id": proposal_id,
            "status": "POLICY_DRAFT_PR_CREATED",
            "merge_performed": True, # This breaks safety!
            "force_push_performed": False,
            "production_direct_write": False,
            "is_draft": True,
            "branch_name": "codex/policy-update",
            "modified_files": ["agents/policy.json"]
        }, f)
        
    with open(p_dir / "policy_apply_preview.json", "w", encoding="utf-8") as f:
        json.dump({"production_apply_performed": False}, f)
        
    with open(p_dir / "policy_draft_pr_plan.json", "w", encoding="utf-8") as f:
        json.dump({"git_operations_performed": False, "files_to_apply": ["agents/policy.json"]}, f)
        
    request = PolicyPRReviewRunRequest(
        operator_id="ADMIN",
        rationale="Running tests",
        risk_acknowledgement=True
    )
    
    report_dict = run_policy_pr_review_gate(proposal_id, request, workspace_dir)
    
    assert report_dict["status"] == "POLICY_PR_REVIEW_BLOCKED"
    assert report_dict["recommended_decision"] == "REQUEST_CHANGES"
    assert len(report_dict["blocking_findings"]) > 0
