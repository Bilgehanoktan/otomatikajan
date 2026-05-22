import pytest
from unittest.mock import patch
from services.project_factory.models import PolicyBoardDecisionRequest
from services.project_factory.policy_board_service import approve_for_preview, request_revision, reject_proposal

@pytest.fixture
def mock_proposals():
    return {
        "generated_at": "2026",
        "proposals": [
            {
                "proposal_id": "POL-1",
                "title": "T1",
                "description": "D1",
                "target_files": ["f1"],
                "proposal_type": "t",
                "risk_level": "HIGH",
                "priority": "HIGH",
                "recommended_changes": [],
                "status": "POLICY_PROPOSAL_DRAFTED",
                "requires_human_gate": True,
                "auto_apply_allowed": False
            }
        ]
    }

@patch("services.project_factory.policy_board_service.write_policy_proposals")
@patch("services.project_factory.policy_board_service.log_policy_board_decision")
@patch("services.project_factory.policy_board_service.load_policy_proposals")
def test_approve_for_preview(mock_load, mock_log, mock_write, mock_proposals):
    mock_load.return_value = mock_proposals
    req = PolicyBoardDecisionRequest(operator_id="op", rationale="rationale", risk_acknowledgement=True)
    res = approve_for_preview("POL-1", req)
    assert res["status"] == "POLICY_BOARD_APPROVED_FOR_PREVIEW"
    mock_write.assert_called_once()
    mock_log.assert_called_once()

def test_approve_for_preview_no_risk_ack():
    req = PolicyBoardDecisionRequest(operator_id="op", rationale="rationale", risk_acknowledgement=False)
    with pytest.raises(ValueError, match="Must acknowledge risks"):
        approve_for_preview("POL-1", req)

@patch("services.project_factory.policy_board_service.write_policy_proposals")
@patch("services.project_factory.policy_board_service.log_policy_board_decision")
@patch("services.project_factory.policy_board_service.load_policy_proposals")
def test_request_revision(mock_load, mock_log, mock_write, mock_proposals):
    mock_load.return_value = mock_proposals
    req = PolicyBoardDecisionRequest(operator_id="op", rationale="rationale")
    res = request_revision("POL-1", req)
    assert res["status"] == "POLICY_BOARD_REVISION_REQUESTED"

@patch("services.project_factory.policy_board_service.write_policy_proposals")
@patch("services.project_factory.policy_board_service.log_policy_board_decision")
@patch("services.project_factory.policy_board_service.load_policy_proposals")
def test_reject_proposal(mock_load, mock_log, mock_write, mock_proposals):
    mock_load.return_value = mock_proposals
    req = PolicyBoardDecisionRequest(operator_id="op", rationale="rationale")
    res = reject_proposal("POL-1", req)
    assert res["status"] == "POLICY_BOARD_REJECTED"
