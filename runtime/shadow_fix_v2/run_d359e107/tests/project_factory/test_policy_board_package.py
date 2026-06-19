import pytest
from unittest.mock import patch
from services.project_factory.policy_board_package import generate_policy_board_package

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
                "status": "POLICY_BOARD_APPROVED_FOR_PREVIEW",
                "requires_human_gate": True,
                "auto_apply_allowed": False
            },
            {
                "proposal_id": "POL-2",
                "title": "T2",
                "description": "D2",
                "target_files": ["f2"],
                "proposal_type": "t",
                "risk_level": "HIGH",
                "priority": "HIGH",
                "recommended_changes": [],
                "status": "POLICY_APPLY_PREVIEW_READY",
                "requires_human_gate": True,
                "auto_apply_allowed": False
            },
            {
                "proposal_id": "POL-3",
                "title": "T3",
                "description": "D3",
                "target_files": ["f3"],
                "proposal_type": "t",
                "risk_level": "HIGH",
                "priority": "HIGH",
                "recommended_changes": [],
                "status": "POLICY_BOARD_REJECTED",
                "requires_human_gate": True,
                "auto_apply_allowed": False
            }
        ]
    }

@patch("services.project_factory.policy_board_package.write_policy_board_package")
@patch("services.project_factory.policy_board_package.load_policy_proposals")
def test_generate_policy_board_package(mock_load, mock_write, mock_proposals):
    mock_load.return_value = mock_proposals
    res = generate_policy_board_package()
    
    assert res["status"] == "POLICY_BOARD_PACKAGE_READY"
    assert res["proposal_count"] == 3
    assert res["approved_for_preview"] == 1
    assert res["preview_ready"] == 1
    assert res["blocked"] == 1
    
    mock_write.assert_called_once()
