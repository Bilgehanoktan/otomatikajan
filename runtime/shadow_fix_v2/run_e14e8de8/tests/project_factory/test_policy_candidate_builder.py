import pytest
from unittest.mock import patch
from services.project_factory.policy_candidate_builder import build_policy_candidates

@patch("services.project_factory.policy_candidate_builder.load_portfolio_intelligence")
@patch("services.project_factory.policy_candidate_builder.write_policy_suggestion_candidates")
def test_build_policy_candidates(mock_write, mock_load):
    mock_load.return_value = {
        "learning_recommendations": [
            {
                "recommendation_id": "REC-1",
                "title": "Missing direct_git_push",
                "priority": "HIGH",
                "target": "configs/external_project_agent_matrix.yaml"
            },
            {
                "recommendation_id": "REC-2",
                "title": "Out of bounds",
                "priority": "LOW",
                "target": "../secrets.json"
            }
        ]
    }
    
    candidates = build_policy_candidates()
    
    # Only 1 should be created, because the 2nd one is out of bounds
    assert len(candidates) == 1
    c = candidates[0]
    
    assert c.target_files == ["configs/external_project_agent_matrix.yaml"]
    assert c.auto_apply_allowed is False
    assert c.requires_human_gate is True
    assert c.risk_level == "HIGH"
    
def test_build_policy_candidates_no_data():
    with patch("services.project_factory.policy_candidate_builder.load_portfolio_intelligence", return_value=None):
        with pytest.raises(ValueError):
            build_policy_candidates()
