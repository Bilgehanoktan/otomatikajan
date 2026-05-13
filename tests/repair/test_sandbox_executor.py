from pathlib import Path

from services.repair.repair_models import RepairCandidate, RepairCase
from services.repair.sandbox_executor import run_patch_in_sandbox


def test_sandbox_rejects_forbidden_changed_file(tmp_path):
    patch_path = tmp_path / "patch.diff"
    patch_path.write_text("", encoding="utf-8")
    case = RepairCase(incident_id="INC-SANDBOX", forbidden_paths=["services/auth/"])
    candidate = RepairCandidate(
        candidate_id="C-FORBIDDEN",
        patch_path=str(patch_path),
        changed_files=["services/auth/router.py"],
    )

    result = run_patch_in_sandbox(candidate, case, repo_root=tmp_path)

    assert result.patch_applied is False
    assert result.tests_passed is False
    assert result.failed_commands == ["forbidden_path_guard"]
    assert result.exit_code == 1


def test_sandbox_rejects_shell_control_operator_in_failed_command(tmp_path, monkeypatch):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "README.md").write_text("sandbox\n", encoding="utf-8")
    patch_path = tmp_path / "patch.diff"
    patch_path.write_text("", encoding="utf-8")
    monkeypatch.setattr("services.repair.sandbox_executor._docker_available", lambda: False)

    case = RepairCase(
        incident_id="INC-CMD",
        failed_command="python -c print(1) && python -c print(2)",
        forbidden_paths=[],
    )
    candidate = RepairCandidate(candidate_id="C-CMD", patch_path=str(patch_path))

    result = run_patch_in_sandbox(candidate, case, repo_root=repo_root)

    assert result.patch_applied is False
    assert result.tests_passed is False
    assert result.exit_code == 1
    assert "unsupported shell control operators" in result.stderr


def test_sandbox_respects_local_temp_backend_when_docker_is_available(tmp_path, monkeypatch):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "README.md").write_text("sandbox\n", encoding="utf-8")
    patch_path = tmp_path / "patch.diff"
    patch_path.write_text("", encoding="utf-8")
    monkeypatch.setenv("SANDBOX_BACKEND", "local_temp")
    monkeypatch.setattr("services.repair.sandbox_executor._docker_available", lambda: True)

    def fail_if_docker_is_used(*_args, **_kwargs):
        raise AssertionError("docker backend should not run when SANDBOX_BACKEND=local_temp")

    monkeypatch.setattr("services.repair.sandbox_executor._run_docker_command", fail_if_docker_is_used)
    case = RepairCase(
        incident_id="INC-LOCAL-TEMP",
        failed_command="python --version",
        forbidden_paths=[],
    )
    candidate = RepairCandidate(candidate_id="C-LOCAL-TEMP", patch_path=str(patch_path))

    result = run_patch_in_sandbox(candidate, case, repo_root=repo_root)

    assert result.patch_applied is True
    assert result.exit_code == 0
