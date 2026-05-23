import json

import pytest

from services.project_factory.artifacts import _resolve_project_dir
from services.project_factory.draft_pr_planner import prepare_draft_pr_plan
from services.project_factory.models import DraftPrPrepareRequest


def _write_preview(tmp_path, project_id, blocking=None):
    project_dir = _resolve_project_dir(project_id, str(tmp_path))
    project_dir.mkdir(parents=True, exist_ok=True)
    preview = {
        "project_id": project_id,
        "status": "APPLY_PREVIEW_READY",
        "production_apply_performed": False,
        "file_changes": [{"path": "src/a.txt", "change_type": "ADD"}],
        "blocking_risks": blocking or [],
    }
    (project_dir / "apply_preview.json").write_text(json.dumps(preview), encoding="utf-8")


def test_prepare_draft_pr_plan_success(tmp_path):
    project_id = "PF-PLAN"
    _write_preview(tmp_path, project_id)
    req = DraftPrPrepareRequest(
        operator_id="op",
        rationale="prepare draft",
        target_branch="main",
        draft_title="Project Factory delivery",
        risk_acknowledgement=True,
    )

    plan = prepare_draft_pr_plan(project_id, req, str(tmp_path))

    assert plan["branch_name"] == "codex/project-factory-PF-PLAN"
    assert plan["git_operations_performed"] is False
    assert plan["files_to_apply"] == ["src/a.txt"]
    project_dir = _resolve_project_dir(project_id, str(tmp_path))
    assert (project_dir / "draft_pr_plan.json").exists()
    assert (project_dir / "draft_pr_decisions.jsonl").exists()


def test_prepare_draft_pr_plan_blocks_preview_risks(tmp_path):
    project_id = "PF-BLOCKED"
    _write_preview(tmp_path, project_id, ["secret_found"])
    req = DraftPrPrepareRequest(
        operator_id="op",
        rationale="prepare draft",
        target_branch="main",
        draft_title="Project Factory delivery",
        risk_acknowledgement=True,
    )

    with pytest.raises(ValueError, match="blocking risks"):
        prepare_draft_pr_plan(project_id, req, str(tmp_path))


def test_prepare_draft_pr_plan_requires_main_or_master(tmp_path):
    project_id = "PF-BRANCH"
    _write_preview(tmp_path, project_id)
    req = DraftPrPrepareRequest(
        operator_id="op",
        rationale="prepare draft",
        target_branch="develop",
        draft_title="Project Factory delivery",
        risk_acknowledgement=True,
    )

    with pytest.raises(ValueError, match="target_branch"):
        prepare_draft_pr_plan(project_id, req, str(tmp_path))
