"""Tests for agent backend integration."""
from __future__ import annotations

import json
from pathlib import Path

from services.repair.agent_backends.base import AgentResult
from services.repair.agent_backends.mock_backend import MockAgentBackend
from services.repair.agent_backends.registry import get_backend, list_backends
from services.repair.repair_models import RepairCase


def test_mock_backend_returns_empty_diff():
    backend = MockAgentBackend()
    case = RepairCase(incident_id="INC-MOCK")
    result = backend.generate_patch(case)

    assert isinstance(result, AgentResult)
    assert result.diff_text == ""
    assert result.changed_files == []
    assert result.confidence == 0.1
    assert result.exit_status == "mock_no_patch"


def test_mock_backend_uses_simulated_patch():
    backend = MockAgentBackend()
    case = RepairCase(
        incident_id="INC-SIM",
        suspected_files=["services/repair/test_file.py"],
        repo_snapshot={"simulated_patch": "--- a/test.py\n+++ b/test.py\n@@ -1 +1 @@\n-old\n+new\n"},
    )
    result = backend.generate_patch(case)

    assert result.diff_text != ""
    assert result.changed_files == ["services/repair/test_file.py"]
    assert result.confidence == 0.45
    assert result.exit_status == "simulated"


def test_registry_returns_mock_by_default():
    backend = get_backend("mock")
    assert backend.name == "mock"


def test_registry_lists_backends():
    names = list_backends()
    assert "mock" in names
    assert len(names) >= 1


def test_registry_falls_back_on_unknown():
    backend = get_backend("nonexistent_backend_xyz")
    assert backend.name == "mock"


def test_agentless_backend_registers():
    names = list_backends()
    assert "agentless" in names


def test_mini_swe_backend_registers():
    names = list_backends()
    assert "mini_swe" in names


def test_all_downloaded_repo_backends_or_patterns_are_registered():
    from services.repair.external_repo_integrations import integration_summary

    names = set(list_backends())
    summary = integration_summary()

    assert "Agentless-main.zip" in summary
    assert "joycode-agent-main.zip" in summary
    assert "SWE-ReX-main.zip" in summary
    assert {"aider", "auto_code_rover", "live_swe", "openhands", "repair_agent", "swe_agent"}.issubset(names)


def test_deferred_backend_returns_no_patch_without_running_agent():
    backend = get_backend("openhands")
    result = backend.generate_patch(RepairCase(incident_id="INC-OPENHANDS"))

    assert result.exit_status == "deferred"
    assert result.diff_text == ""
    assert result.error


def test_agentless_backend_no_suspected_files():
    """Agentless backend should return error when no suspected files."""
    from services.repair.agent_backends.agentless_backend import AgentlessBackend

    backend = AgentlessBackend()
    case = RepairCase(incident_id="INC-EMPTY", suspected_files=[])
    result = backend.generate_patch(case)

    assert result.exit_status == "no_targets"
    assert result.error


def test_agentless_search_replace_parser():
    """Test that the SEARCH/REPLACE parser extracts edits correctly."""
    from services.repair.agent_backends.agentless_backend import _parse_search_replace

    raw = """
Here's the fix:

### services/repair/code_localizer.py
<<<<<<< SEARCH
    if not normalized:
        return False
=======
    if not normalized:
        return True
>>>>>>> REPLACE

### services/repair/risk_adapter.py
<<<<<<< SEARCH
    score = 0.2
=======
    score = 0.15
>>>>>>> REPLACE
"""
    edits = _parse_search_replace(raw)
    assert len(edits) == 2
    assert edits[0]["file"] == "services/repair/code_localizer.py"
    assert "return False" in edits[0]["search"]
    assert "return True" in edits[0]["replace"]
    assert edits[1]["file"] == "services/repair/risk_adapter.py"


def test_agentless_apply_edits():
    """Test that edits are applied correctly to file content."""
    from services.repair.agent_backends.agentless_backend import _apply_edits_to_content

    content = "def foo():\n    return False\n"
    edits = [
        {"file": "test.py", "search": "return False", "replace": "return True"},
    ]
    new_content, changed = _apply_edits_to_content(content, edits, "test.py")
    assert changed
    assert "return True" in new_content
    assert "return False" not in new_content


def test_agentless_generate_diff():
    """Test unified diff generation."""
    from services.repair.agent_backends.agentless_backend import _generate_unified_diff

    original = "line1\nline2\nline3\n"
    modified = "line1\nline2_fixed\nline3\n"
    diff = _generate_unified_diff(original, modified, "test.py")
    assert "--- a/test.py" in diff
    assert "+++ b/test.py" in diff
    assert "-line2" in diff
    assert "+line2_fixed" in diff


def test_mini_swe_command_extraction():
    """Test bash command extraction from LLM responses."""
    from services.repair.agent_backends.mini_swe_backend import _extract_commands

    response = """
Let me examine the file:

```bash
cat services/repair/code_localizer.py
```

And also check the test:

```bash
python -m pytest tests/repair/test_code_localizer.py -v
```
"""
    commands = _extract_commands(response)
    assert len(commands) == 2
    assert "cat services/repair/code_localizer.py" in commands[0]
    assert "pytest" in commands[1]


def test_mini_swe_submission_detection():
    """Test detection of task submission signal."""
    from services.repair.agent_backends.mini_swe_backend import _check_submission

    # Not a submission
    assert _check_submission("just regular text") is None

    # Submission
    result = _check_submission(
        "Done.\necho COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT\n--- a/test.py\n+++ b/test.py"
    )
    assert result is not None
    assert "--- a/test.py" in result


def test_mini_swe_command_validation():
    """Test command safety validation."""
    from services.repair.agent_backends.mini_swe_backend import _validate_command

    assert _validate_command("python -m pytest tests/") is True
    assert _validate_command("cat README.md") is True
    assert _validate_command("grep -r 'error' services/") is True
    assert _validate_command("rm -rf /") is False


def test_patch_candidate_runner_uses_backend(tmp_path):
    """Test that patch_candidate_runner dispatches to the mock backend."""
    from services.repair.patch_candidate_runner import generate_patch_candidate

    case = RepairCase(
        incident_id="INC-BACKEND",
        traceback='File "services/repair/code_localizer.py", line 10',
        suspected_files=["services/repair/code_localizer.py"],
        repo_snapshot={"_repair_output_root": str(tmp_path)},
    )

    candidate = generate_patch_candidate(case, backend_name="mock")

    assert candidate.candidate_id.startswith("RC-")
    assert candidate.status == "PATCH_PROPOSED"
    assert Path(candidate.patch_path).exists()
    assert (tmp_path / "INC-BACKEND" / "repair_prompt.rendered.md").exists()


def test_patch_candidate_runner_honors_mini_swe_mode_without_backend_env(tmp_path, monkeypatch):
    from services.repair.patch_candidate_runner import generate_patch_candidate

    monkeypatch.delenv("REPAIR_AGENT_BACKEND", raising=False)
    monkeypatch.setenv("MINI_SWE_MODE", "real")
    case = RepairCase(
        incident_id="INC-MINI-MODE",
        repo_snapshot={"_repair_output_root": str(tmp_path)},
    )

    candidate = generate_patch_candidate(case)

    assert Path(candidate.patch_path).exists()
    assert "mini-swe-agent real mode" in candidate.agent_summary
    assert (tmp_path / "INC-MINI-MODE" / "agent_trajectory.log").exists()
