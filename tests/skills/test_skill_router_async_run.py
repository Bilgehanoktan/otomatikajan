import pytest

from packages.skills.base import SkillRequest
from packages.skills.router import skill_router
from packages.skills.registry import skill_registry


@pytest.mark.asyncio
async def test_skill_router_run_suggested_returns_results_for_bug_task(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    req = SkillRequest(
        task_type="generic",
        title="repair_router traceback bug",
        description="traceback occurs in repair flow bug",
        project_id="p1",
        context={},
    )

    results = await skill_router.run_suggested(req)

    assert isinstance(results, list)
    assert len(results) >= 1
    ids = [r.skill_id for r in results]
    assert "file_search" in ids or "vault_memory" in ids or "debugging" in ids
