from __future__ import annotations

from services.repair.external_repo_integrations import (
    load_external_agent_catalog,
    validate_agent_execution,
)


def test_catalog_loads_successfully():
    """Verify that catalog configuration loads successfully and matches structural rules."""
    catalog = load_external_agent_catalog()
    assert "external_agents" in catalog
    agents = catalog["external_agents"]
    
    assert "swe_agent" in agents
    assert "swe_rex" in agents
    assert "pr_agent" in agents
    assert "stagehand" in agents
    assert "openhands" in agents
    assert "github_copilot" in agents


def test_agent_schema_fields():
    """Verify that catalog agents have all required Phase 32 governance fields."""
    catalog = load_external_agent_catalog()
    agents = catalog["external_agents"]
    
    for key, info in agents.items():
        assert "name" in info
        assert "repo_url" in info
        assert "pinned_commit" in info
        assert "license" in info
        assert "purpose" in info
        assert "risk_level" in info
        assert "allowed_modes" in info
        assert "forbidden_actions" in info
        
        assert isinstance(info["allowed_modes"], list)
        assert isinstance(info["forbidden_actions"], list)


def test_validate_allowed_modes():
    """Verify that allowed modes are successfully approved."""
    # Test PR-Agent review_gate mode
    res = validate_agent_execution("pr_agent", "review_gate")
    assert res["valid"] is True
    assert res["status"] == "APPROVED_GATED"
    assert "bypass_human_gate" in res["forbidden_actions"]
    
    # Test SWE-ReX sandbox_runner mode
    res = validate_agent_execution("swe_rex", "sandbox_runner")
    assert res["valid"] is True
    assert res["status"] == "APPROVED_GATED"
    assert "production_db_modify" in res["forbidden_actions"]


def test_validate_forbidden_modes():
    """Verify that modes not permitted for an agent are rejected."""
    # PR-Agent should not be allowed to run as sandbox_runner
    res = validate_agent_execution("pr_agent", "sandbox_runner")
    assert res["valid"] is False
    assert res["status"] == "BLOCKED"
    assert "Mode 'sandbox_runner' is not allowed" in res["reason"]


def test_proprietary_agent_restrictions():
    """Verify that proprietary agents like GitHub Copilot are restricted to reference_only."""
    # Copilot reference_only should be allowed
    res = validate_agent_execution("github_copilot", "reference_only")
    assert res["valid"] is True
    assert res["status"] == "APPROVED_GATED"
    
    # Copilot local_adapter should be blocked
    res = validate_agent_execution("github_copilot", "local_adapter")
    assert res["valid"] is False
    assert res["status"] == "BLOCKED"
    assert "restricted to 'reference_only'" in res["reason"]


def test_unregistered_agent_blocking():
    """Verify that unregistered agents are blocked."""
    res = validate_agent_execution("unknown_super_agent", "experimental")
    assert res["valid"] is False
    assert res["status"] == "BLOCKED"
    assert "is not registered in the external agent catalog" in res["reason"]


def test_high_risk_agent_warnings():
    """Verify that high-risk agents generate high-risk warnings requiring strict approvals."""
    # SWE-Agent is classified as high-risk
    res = validate_agent_execution("swe_agent", "local_adapter")
    assert res["valid"] is True
    assert res["status"] == "WARNING_HIGH_RISK"
    assert "HIGH RISK" in res["reason"]


def test_generate_patch_candidate_blocked_agent(tmp_path):
    """Verify that generate_patch_candidate raises PermissionError when a blocked agent configuration is triggered."""
    import pytest
    from services.repair.patch_candidate_runner import generate_patch_candidate
    from services.repair.repair_models import RepairCase

    case = RepairCase(
        incident_id="INC-TEST-BLOCKED",
        trace_id="TRACE-TEST-BLOCKED",
        error_type="AssertionError",
        summary="blocked agent smoke",
        failed_command="",
        failed_test="some_test",
        traceback="",
        suspected_files=[],
        repo_snapshot={"_repair_output_root": str(tmp_path)}
    )

    # github_copilot with local_adapter is blocked by the catalog
    with pytest.raises(PermissionError) as exc_info:
        generate_patch_candidate(case, backend_name="github_copilot")
    assert "Phase 32 External Agent Intake Policy Violation" in str(exc_info.value)
    assert "restricted to 'reference_only'" in str(exc_info.value)


def test_generate_patch_candidate_unregistered_agent(tmp_path):
    """Verify that generate_patch_candidate raises PermissionError when an unregistered agent is triggered."""
    import pytest
    from services.repair.patch_candidate_runner import generate_patch_candidate
    from services.repair.repair_models import RepairCase

    case = RepairCase(
        incident_id="INC-TEST-UNREG",
        trace_id="TRACE-TEST-UNREG",
        error_type="AssertionError",
        summary="unregistered agent smoke",
        failed_command="",
        failed_test="some_test",
        traceback="",
        suspected_files=[],
        repo_snapshot={"_repair_output_root": str(tmp_path)}
    )

    # unregistered agent is blocked
    with pytest.raises(PermissionError) as exc_info:
        generate_patch_candidate(case, backend_name="unregistered_super_agent")
    assert "is not registered in the external agent catalog" in str(exc_info.value)

