from skills.base import SkillRequest
from skills.router import skill_router


def test_skill_router_bug_task_suggests_debugging_file_search_vault():
    req = SkillRequest(
        task_type="generic",
        title="repair_router async bug",
        description="traceback occurs in repair flow",
    )

    suggested = skill_router.suggest(req)

    assert "debugging" in suggested
    assert "file_search" in suggested
    assert "vault_memory" in suggested


def test_skill_router_repo_task_suggests_file_search_and_optimization():
    req = SkillRequest(
        task_type="generic",
        title="repo impact analysis",
        description="find dependency impact in codebase",
    )

    suggested = skill_router.suggest(req)

    assert "file_search" in suggested
    assert "optimization" in suggested


def test_skill_router_context_task_suggests_optimization_and_vault():
    req = SkillRequest(
        task_type="generic",
        title="optimize prompt context",
        description="reduce token usage and memory noise",
    )

    suggested = skill_router.suggest(req)

    assert "optimization" in suggested
    assert "vault_memory" in suggested


def test_skill_router_reusable_task_suggests_skill_creator():
    req = SkillRequest(
        task_type="generic",
        title="create reusable workflow template",
        description="repeated repair workflow should become a new skill",
    )

    suggested = skill_router.suggest(req)

    assert "skill_creator" in suggested


def test_skill_router_does_not_return_duplicates():
    req = SkillRequest(
        task_type="generic",
        title="bug in prompt memory context",
        description="traceback while optimizing prompt memory context and bug recovery",
    )

    suggested = skill_router.suggest(req)

    assert len(suggested) == len(set(suggested))
