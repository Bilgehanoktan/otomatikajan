from __future__ import annotations

import json
from pathlib import Path
import pytest

from services.repair.external_agents.models import ExternalAgentContext, ExternalAgentResult
from services.repair.external_agents.registry import ExternalAgentRegistry
from services.repair.external_agents.mock_adapter import MockExternalAgentAdapter
from services.repair.external_agents.base import ExternalAgentAdapter
from services.repair.patch_candidate_runner import generate_patch_candidate
from services.repair.repair_models import RepairCase


def test_mock_external_adapter_returns_result_artifact(tmp_path):
    """Verify that MockExternalAgentAdapter correctly runs and generates all specified artifact files."""
    adapter = MockExternalAgentAdapter()
    
    ctx = ExternalAgentContext(
        incident_id="INC-MOCK-RUN",
        repair_case_id="CASE-123",
        agent_key="swe_agent",
        requested_mode="local_adapter",
        allowed_tools=["services/"],
        forbidden_actions=["direct_git_push"],
        output_dir=str(tmp_path),
    )
    
    result = adapter.run(ctx)
    
    assert result.status == "COMPLETED"
    assert result.candidate_source == "swe_agent"
    assert result.confidence_score == 0.9
    
    # Verify file structures are created
    agent_dir = tmp_path / "INC-MOCK-RUN" / "external_agents" / "swe_agent"
    assert agent_dir.exists()
    
    assert (agent_dir / "input_artifact.json").exists()
    assert (agent_dir / "patch_candidate.diff").exists()
    assert (agent_dir / "external_agent_result.json").exists()
    assert (agent_dir / "external_agent_trace.json").exists()
    assert (agent_dir / "risk_notes.json").exists()
    
    # Read output content to verify structural matching
    trace_data = json.loads((agent_dir / "external_agent_trace.json").read_text(encoding="utf-8"))
    assert "steps" in trace_data
    
    risk_data = json.loads((agent_dir / "risk_notes.json").read_text(encoding="utf-8"))
    assert "analyzed_paths" in risk_data


def test_external_agent_registry_blocks_unknown_agent():
    """Verify that ExternalAgentRegistry prevents registration of agents not in external_agent_catalog.yaml."""
    class InvalidAdapter(ExternalAgentAdapter):
        @property
        def agent_key(self) -> str:
            return "rogue_unregistered_agent"
        
        @property
        def supported_modes(self) -> list[str]:
            return ["experimental"]
        
        def run(self, context): pass
        def validate_context(self, context): pass
        def build_artifacts(self, result): pass

    # Attempting to register unregistered agent must fail
    with pytest.raises(PermissionError) as exc_info:
        ExternalAgentRegistry.register(InvalidAdapter())
    assert "is not registered in the external agent catalog" in str(exc_info.value)

    # Attempting to fetch unknown agent must fail
    with pytest.raises(PermissionError) as exc_info2:
        ExternalAgentRegistry.get_adapter("unknown_missing_agent")
    assert "is unknown or not registered" in str(exc_info2.value)


def test_external_agent_context_requires_incident_id():
    """Verify that ExternalAgentContext validation requires a non-empty incident_id."""
    with pytest.raises(ValueError) as exc_info:
        ExternalAgentContext(
            incident_id="",
            repair_case_id="CASE-1",
            agent_key="swe_agent",
            requested_mode="local_adapter",
        )
    assert "incident_id is required" in str(exc_info.value)


def test_external_agent_result_serializes_stable_payload():
    """Verify that ExternalAgentResult successfully serializes to a dict with all expected fields."""
    res = ExternalAgentResult(
        status="COMPLETED",
        candidate_source="swe_agent",
        output_artifact="/path/to/artifact.diff",
        confidence_score=0.85,
        evidence_refs=["/path/to/trace.json"],
        cost=0.05,
        duration_ms=1200.0,
        risk="low",
        warnings=["minor_issue"],
        blocked_reason=None,
    )
    
    serialized = res.to_dict()
    assert isinstance(serialized, dict)
    assert serialized["status"] == "COMPLETED"
    assert serialized["candidate_source"] == "swe_agent"
    assert serialized["output_artifact"] == "/path/to/artifact.diff"
    assert serialized["confidence_score"] == 0.85
    assert serialized["cost"] == 0.05
    assert serialized["duration_ms"] == 1200.0
    assert serialized["risk"] == "low"
    assert "minor_issue" in serialized["warnings"]
    assert serialized["blocked_reason"] is None


def test_patch_candidate_runner_uses_external_adapter_after_catalog_validation(tmp_path):
    """Verify that patch_candidate_runner validates, retrieves, and runs the registered adapter."""
    # Ensure swe_agent is registered (lazy load will trigger it)
    ExternalAgentRegistry.clear()
    
    case = RepairCase(
        incident_id="INC-RUNNER-TEST",
        trace_id="TRACE-1",
        error_type="AssertionError",
        summary="runner integration",
        failed_command="",
        failed_test="...",
        traceback="",
        suspected_files=[],
        repo_snapshot={"_repair_output_root": str(tmp_path)}
    )
    
    candidate = generate_patch_candidate(case, backend_name="swe_agent")
    
    assert candidate.status == "PATCH_PROPOSED"
    assert candidate.confidence == 0.9
    assert "swe_agent" in candidate.agent_summary
    
    # Check that diff artifact is located inside external_agents folder
    patch_path = Path(candidate.patch_path)
    assert patch_path.exists()
    assert "external_agents" in patch_path.parts
    assert "swe_agent" in patch_path.parts


def test_blocked_external_agent_does_not_create_patch_candidate(tmp_path):
    """Verify that blocked external agent execution never creates a patch candidate."""
    # Register a temporary adapter for 'swe_rex' which returns BLOCKED status
    class BlockedMockAdapter(ExternalAgentAdapter):
        @property
        def agent_key(self) -> str:
            return "swe_rex"

        @property
        def supported_modes(self) -> list[str]:
            return ["sandbox_runner"]

        def run(self, context: ExternalAgentContext) -> ExternalAgentResult:
            return ExternalAgentResult(
                status="BLOCKED",
                candidate_source=self.agent_key,
                blocked_reason="Governance constraint violation (sandbox resource limitation)",
            )

        def validate_context(self, context: ExternalAgentContext) -> None: pass
        def build_artifacts(self, result: ExternalAgentResult) -> dict: return {}

    # Register in registry
    ExternalAgentRegistry.register(BlockedMockAdapter())

    case = RepairCase(
        incident_id="INC-BLOCKED-RUNNER",
        trace_id="TRACE-2",
        error_type="AssertionError",
        summary="blocked runner test",
        failed_command="",
        failed_test="...",
        traceback="",
        suspected_files=[],
        repo_snapshot={"_repair_output_root": str(tmp_path)}
    )

    # Dispatching to 'swe_rex' should raise PermissionError due to the BLOCKED status returned by adapter
    with pytest.raises(PermissionError) as exc_info:
        generate_patch_candidate(case, backend_name="swe_rex")
    
    assert "External agent execution returned non-successful status" in str(exc_info.value)
    assert "Governance constraint violation" in str(exc_info.value)
    
    # Assert that no patch candidate file is generated for this incident under outputs
    patch_candidate_file = tmp_path / "INC-BLOCKED-RUNNER" / "patch.diff"
    assert not patch_candidate_file.exists()
