import pytest
import os
import json
import tempfile
from services.project_factory.models import PolicyPRReviewDecisionRequest
from services.project_factory.policy_pr_review_decision import execute_policy_pr_review_decision
from services.project_factory.artifacts import _resolve_policy_autopilot_dir

@pytest.fixture
def workspace_dir():
    with tempfile.TemporaryDirectory() as temp_dir:
        p_dir = _resolve_policy_autopilot_dir(temp_dir)
        p_dir.mkdir(parents=True, exist_ok=True)
        yield temp_dir

def test_execute_decision_success(workspace_dir):
    p_dir = _resolve_policy_autopilot_dir(workspace_dir)
    proposal_id = "POL-1"
    
    with open(p_dir / "policy_pr_review_report.json", "w", encoding="utf-8") as f:
        json.dump({
            "proposal_id": proposal_id,
            "status": "POLICY_PR_REVIEW_PASSED"
        }, f)
        
    request = PolicyPRReviewDecisionRequest(
        operator_id="ADMIN",
        decision="MARK_REVIEWED",
        rationale="Looks good",
        risk_acknowledgement=True
    )
    
    result = execute_policy_pr_review_decision(proposal_id, request, workspace_dir)
    
    assert result["new_status"] == "POLICY_READY_FOR_FINAL_DECISION"
    assert result["decision"] == "MARK_REVIEWED"
    
    # Check that status file is updated
    with open(p_dir / "policy_pr_status.json", "r", encoding="utf-8") as f:
        status_data = json.load(f)
        assert status_data["status"] == "POLICY_READY_FOR_FINAL_DECISION"

def test_execute_decision_invalid(workspace_dir):
    p_dir = _resolve_policy_autopilot_dir(workspace_dir)
    proposal_id = "POL-1"
    
    with open(p_dir / "policy_pr_review_report.json", "w", encoding="utf-8") as f:
        json.dump({"proposal_id": proposal_id}, f)
        
    request = PolicyPRReviewDecisionRequest(
        operator_id="ADMIN",
        decision="UNKNOWN_DECISION",
        rationale="Looks good",
        risk_acknowledgement=True
    )
    
    with pytest.raises(ValueError):
        execute_policy_pr_review_decision(proposal_id, request, workspace_dir)

def test_mark_reviewed_blocks_failed_report(workspace_dir):
    p_dir = _resolve_policy_autopilot_dir(workspace_dir)
    proposal_id = "POL-1"

    with open(p_dir / "policy_pr_review_report.json", "w", encoding="utf-8") as f:
        json.dump({
            "proposal_id": proposal_id,
            "status": "POLICY_PR_REVIEW_BLOCKED",
            "blocking_findings": ["Verifier Mesh Failed: modified_files_scope"],
        }, f)

    request = PolicyPRReviewDecisionRequest(
        operator_id="ADMIN",
        decision="MARK_REVIEWED",
        rationale="Override blocked report",
        risk_acknowledgement=True
    )

    with pytest.raises(ValueError, match="Cannot mark reviewed"):
        execute_policy_pr_review_decision(proposal_id, request, workspace_dir)
