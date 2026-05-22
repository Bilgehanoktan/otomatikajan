import pytest
from unittest.mock import patch, MagicMock
from services.project_factory.models import RunPolicyAutopilotRequest, PolicyProposalDecisionRequest
from services.project_factory.policy_autopilot import (
    run_policy_autopilot,
    approve_for_policy_board,
    defer_policy_proposal,
    reject_policy_proposal
)

@patch("services.project_factory.policy_autopilot.build_policy_candidates")
@patch("services.project_factory.policy_autopilot.analyze_policy_impact")
@patch("services.project_factory.policy_autopilot.assess_policy_risk")
@patch("services.project_factory.policy_autopilot.compile_policy_proposals")
@patch("services.project_factory.policy_autopilot.log_policy_autopilot_event")
def test_run_policy_autopilot(mock_log, mock_compile, mock_risk, mock_impact, mock_build):
    mock_build.return_value = []
    mock_compile.return_value = MagicMock(model_dump=lambda: {"proposals": []})
    
    req = RunPolicyAutopilotRequest(operator_id="test", rationale="test run")
    res = run_policy_autopilot(req)
    
    assert res["status"] == "success"
    mock_log.assert_called_once()
    mock_compile.assert_called_once()

@patch("services.project_factory.policy_autopilot.update_proposal_status")
@patch("services.project_factory.policy_autopilot.log_policy_autopilot_event")
def test_approve_for_policy_board(mock_log, mock_update):
    mock_update.return_value = MagicMock(model_dump=lambda: {"id": "1"})
    
    req = PolicyProposalDecisionRequest(operator_id="test", rationale="test approve", risk_acknowledgement=True)
    res = approve_for_policy_board("POL-1", req)
    
    assert res["status"] == "success"
    mock_update.assert_called_once_with("POL-1", "POLICY_PROPOSAL_APPROVED_FOR_BOARD", None)

def test_approve_for_policy_board_missing_ack():
    req = PolicyProposalDecisionRequest(operator_id="test", rationale="test approve", risk_acknowledgement=False)
    with pytest.raises(ValueError):
        approve_for_policy_board("POL-1", req)
