from pathlib import Path

import pytest

from services.project_factory.git_workspace import GitSafetyViolation, GitWorkspaceExecutor
from services.project_factory.artifacts import _resolve_project_dir


def test_apply_delivery_files_rejects_path_traversal_source_and_target(tmp_path):
    workspace = tmp_path
    project_id = "PF-GIT"
    project_dir = _resolve_project_dir(project_id, str(workspace))
    delivery_dir = project_dir / "delivery_package" / "files"
    delivery_dir.mkdir(parents=True, exist_ok=True)
    (delivery_dir / "safe.txt").write_text("safe", encoding="utf-8")

    executor = GitWorkspaceExecutor(str(workspace))

    with pytest.raises(GitSafetyViolation, match="Path traversal"):
        executor.apply_delivery_files(project_id, ["../outside.txt"])


def test_pr_safety_rejects_protected_files(monkeypatch):
    from services.project_factory.pr_safety import validate_pr_creation_safety

    monkeypatch.setattr("services.project_factory.pr_safety.load_delivery_manifest", lambda p, r: {"production_apply_allowed": False})
    monkeypatch.setattr("services.project_factory.pr_safety.load_apply_preview", lambda p, r: {"blocking_risks": [], "production_apply_performed": False})
    monkeypatch.setattr(
        "services.project_factory.pr_safety.load_draft_pr_plan",
        lambda p, r: {"branch_name": "codex/pf", "target_branch": "main", "files_to_apply": [".env"]},
    )

    with pytest.raises(ValueError, match="protected file"):
        validate_pr_creation_safety("PF-1", "op", "valid rationale", True, "root")
