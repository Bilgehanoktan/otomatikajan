import pytest
from unittest.mock import patch
from services.project_factory.policy_apply_preview import generate_apply_preview

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
                "status": "POLICY_PROPOSAL_DRAFTED",
                "requires_human_gate": True,
                "auto_apply_allowed": False
            }
        ]
    }

@patch("services.project_factory.policy_apply_preview.write_policy_apply_preview")
@patch("services.project_factory.policy_apply_preview.build_policy_diff_summary")
@patch("services.project_factory.policy_apply_preview.load_policy_proposals")
def test_generate_apply_preview(mock_load, mock_build, mock_write, mock_proposals):
    mock_load.return_value = mock_proposals
    res = generate_apply_preview("POL-1")
    assert res["status"] == "POLICY_APPLY_PREVIEW_READY"
    assert res["production_apply_performed"] == False
    assert res["policy_files_modified"] == False
    mock_write.assert_called_once()
    mock_build.assert_called_once()

@patch("services.project_factory.policy_apply_preview.load_policy_proposals")
def test_generate_apply_preview_not_approved(mock_load, mock_proposals):
    mock_load.return_value = mock_proposals
    with pytest.raises(ValueError, match="must be APPROVED_FOR_PREVIEW"):
        generate_apply_preview("POL-2")
