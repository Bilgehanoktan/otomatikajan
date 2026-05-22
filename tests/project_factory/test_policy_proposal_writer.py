import pytest
from unittest.mock import patch
from services.project_factory.models import PolicyProposal
from services.project_factory.policy_proposal_writer import compile_policy_proposals, update_proposal_status

@patch("services.project_factory.policy_proposal_writer.write_policy_proposals")
def test_compile_policy_proposals(mock_write):
    prop1 = PolicyProposal(
        proposal_id="POL-1",
        title="T1",
        description="D1",
        target_files=["f1"],
        proposal_type="t",
        risk_level="HIGH",
        priority="HIGH",
        recommended_changes=[],
        status="s",
        requires_human_gate=True,
        auto_apply_allowed=False
    )
    
    col = compile_policy_proposals([prop1])
    assert len(col.proposals) == 1
    assert col.proposals[0].proposal_id == "POL-1"

@patch("services.project_factory.policy_proposal_writer.write_policy_proposals")
@patch("services.project_factory.policy_proposal_writer.load_policy_proposals")
def test_update_proposal_status(mock_load, mock_write):
    mock_load.return_value = {
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
                "status": "POLICY_SUGGESTIONS_READY",
                "requires_human_gate": True,
                "auto_apply_allowed": False
            }
        ]
    }
    
    updated = update_proposal_status("POL-1", "POLICY_PROPOSAL_REJECTED")
    assert updated.status == "POLICY_PROPOSAL_REJECTED"
    mock_write.assert_called_once()
