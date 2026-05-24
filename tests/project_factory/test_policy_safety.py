import pytest
from services.project_factory.models import PolicyProposal, RecommendedChange
from services.project_factory.policy_safety import check_policy_safety

def test_policy_safety_auto_apply():
    p = PolicyProposal(
        proposal_id="p1",
        title="t",
        description="d",
        target_files=["config/test.yaml"],
        proposal_type="t",
        risk_level="HIGH",
        priority="HIGH",
        recommended_changes=[],
        status="s",
        requires_human_gate=True,
        auto_apply_allowed=True
    )
    risks = check_policy_safety(p)
    assert any("auto_apply_allowed must be false" in r for r in risks)

def test_policy_safety_out_of_bounds():
    p = PolicyProposal(
        proposal_id="p1",
        title="t",
        description="d",
        target_files=["../config/test.yaml", "/etc/passwd"],
        proposal_type="t",
        risk_level="HIGH",
        priority="HIGH",
        recommended_changes=[],
        status="s",
        requires_human_gate=True,
        auto_apply_allowed=False
    )
    risks = check_policy_safety(p)
    assert any("out of workspace bounds" in r for r in risks)

def test_policy_safety_windows_absolute_path_out_of_bounds():
    p = PolicyProposal(
        proposal_id="p1",
        title="t",
        description="d",
        target_files=[r"C:\outside\policy.yaml", r"\absolute\policy.yaml"],
        proposal_type="t",
        risk_level="HIGH",
        priority="HIGH",
        recommended_changes=[],
        status="s",
        requires_human_gate=True,
        auto_apply_allowed=False
    )
    risks = check_policy_safety(p)
    assert sum("out of workspace bounds" in r for r in risks) == 2

def test_policy_safety_sensitive_files():
    p = PolicyProposal(
        proposal_id="p1",
        title="t",
        description="d",
        target_files=[".env", "secret.json", "key.pem", "db.sqlite"],
        proposal_type="t",
        risk_level="HIGH",
        priority="HIGH",
        recommended_changes=[],
        status="s",
        requires_human_gate=True,
        auto_apply_allowed=False
    )
    risks = check_policy_safety(p)
    assert len(risks) == 4

def test_policy_safety_delete_operation():
    p = PolicyProposal(
        proposal_id="p1",
        title="t",
        description="d",
        target_files=["config/test.yaml"],
        proposal_type="t",
        risk_level="HIGH",
        priority="HIGH",
        recommended_changes=[RecommendedChange(field="f", remove=["x"])],
        status="s",
        requires_human_gate=True,
        auto_apply_allowed=False
    )
    risks = check_policy_safety(p)
    assert any("Delete operations are blocked" in r for r in risks)
