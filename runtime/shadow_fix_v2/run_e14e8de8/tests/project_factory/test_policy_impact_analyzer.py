import pytest
from unittest.mock import patch
from services.project_factory.models import PolicyProposal, RecommendedChange
from services.project_factory.policy_impact_analyzer import analyze_policy_impact

@patch("services.project_factory.policy_impact_analyzer.write_policy_impact_analysis")
def test_analyze_policy_impact(mock_write):
    prop1 = PolicyProposal(
        proposal_id="POL-1",
        title="T1",
        description="D1",
        target_files=["configs/external_project_agent_matrix.yaml"],
        proposal_type="t",
        risk_level="HIGH",
        priority="HIGH",
        recommended_changes=[],
        status="s",
        requires_human_gate=True,
        auto_apply_allowed=False
    )
    
    impacts = analyze_policy_impact([prop1])
    assert len(impacts) == 1
    
    i = impacts[0]
    assert i.proposal_id == "POL-1"
    assert "openhands" in i.affected_agents
    assert i.rollback_plan_required is True
