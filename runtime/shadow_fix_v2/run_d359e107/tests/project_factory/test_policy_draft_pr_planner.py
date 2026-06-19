import pytest
from unittest.mock import patch
from services.project_factory.models import PolicyDraftPRPlanRequest
from services.project_factory.policy_draft_pr_planner import prepare_draft_pr_plan

@pytest.fixture
def mock_preview():
    return {
        "proposal_id": "POL-1",
        "production_apply_performed": False,
        "policy_files_modified": False,
        "blocking_risks": []
    }

@pytest.fixture
def mock_proposals():
    return {
        "proposals": [
            {
                "proposal_id": "POL-1",
                "status": "POLICY_APPLY_PREVIEW_READY",
                "target_files": ["f1.yaml"],
                "description": "d1",
                "auto_apply_allowed": False
            }
        ]
    }

@patch("services.project_factory.policy_draft_pr_planner.check_policy_pr_plan_safety")
@patch("services.project_factory.policy_draft_pr_planner.log_policy_pr_plan")
@patch("services.project_factory.policy_draft_pr_planner.write_policy_draft_pr_plan")
@patch("services.project_factory.policy_draft_pr_planner.load_policy_proposals")
@patch("services.project_factory.policy_draft_pr_planner.load_policy_apply_preview")
def test_prepare_draft_pr_plan_success(mock_preview_fn, mock_proposals_fn, mock_write, mock_log, mock_check, mock_preview, mock_proposals):
    mock_preview_fn.return_value = mock_preview
    mock_proposals_fn.return_value = mock_proposals
    mock_check.return_value = [] # no risks
    
    req = PolicyDraftPRPlanRequest(operator_id="op", rationale="rationale", draft_title="title", risk_acknowledgement=True)
    plan = prepare_draft_pr_plan("POL-1", req)
    
    assert plan["status"] == "POLICY_DRAFT_PR_PLAN_READY"
    assert plan["branch_name"] == "codex/policy-POL-1"
    assert plan["git_operations_performed"] == False
    assert plan["policy_files_modified"] == False
    
    mock_write.assert_called_once()
    mock_log.assert_called_once()

@patch("services.project_factory.policy_draft_pr_planner.check_policy_pr_plan_safety")
@patch("services.project_factory.policy_draft_pr_planner.log_policy_pr_plan")
@patch("services.project_factory.policy_draft_pr_planner.load_policy_proposals")
@patch("services.project_factory.policy_draft_pr_planner.load_policy_apply_preview")
def test_prepare_draft_pr_plan_blocked_by_safety(mock_preview_fn, mock_proposals_fn, mock_log, mock_check, mock_preview, mock_proposals):
    mock_preview_fn.return_value = mock_preview
    mock_proposals_fn.return_value = mock_proposals
    mock_check.return_value = ["Blocking risk found"]
    
    req = PolicyDraftPRPlanRequest(operator_id="op", rationale="rationale", draft_title="title", risk_acknowledgement=True)
    
    with pytest.raises(ValueError, match="Safety checks failed"):
        prepare_draft_pr_plan("POL-1", req)
        
    mock_log.assert_called_once()
