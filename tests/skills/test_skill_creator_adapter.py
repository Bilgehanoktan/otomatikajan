from pathlib import Path

import pytest

from skills.base import SkillRequest
from skills.adapters.skill_creator_adapter import SkillCreatorSkillAdapter


@pytest.mark.asyncio
async def test_skill_creator_creates_draft_skill_files(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    adapter = SkillCreatorSkillAdapter()
    req = SkillRequest(
        task_type="generic",
        title="Create Reusable Workflow Template",
        description="Repeated recovery flow should become a reusable skill",
    )

    result = await adapter.execute(req)

    assert result.success is True

    skill_md = Path(result.data["path"])
    manifest = Path(result.data["manifest"])

    assert skill_md.exists()
    assert manifest.exists()

    skill_content = skill_md.read_text(encoding="utf-8")
    manifest_content = manifest.read_text(encoding="utf-8")

    assert "Create Reusable Workflow Template" in skill_content
    assert "Repeated recovery flow should become a reusable skill" in skill_content
    assert '"status": "draft"' in manifest_content
    assert '"approval_required": true' in manifest_content


def test_skill_creator_can_handle_reusable_workflow():
    adapter = SkillCreatorSkillAdapter()

    req = SkillRequest(
        task_type="generic",
        title="create reusable workflow",
        description="new skill template for repeated jobs",
    )
    assert adapter.can_handle(req) is True


def test_skill_creator_ignores_normal_bug_task():
    adapter = SkillCreatorSkillAdapter()

    req = SkillRequest(
        task_type="generic",
        title="fix celery import bug",
        description="repair traceback in worker startup",
    )
    assert adapter.can_handle(req) is False
