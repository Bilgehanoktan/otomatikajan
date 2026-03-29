from pathlib import Path


def test_task_write_router_contains_skill_integration_contract():
    content = Path("api/task_write_router.py").read_text(encoding="utf-8")

    assert "from skills.base import SkillRequest" in content
    assert "from skills.router import skill_router" in content
    assert "suggested_skills" in content
    assert "skill_router.suggest(" in content


def test_orchestrator_contains_skill_preflight_contract():
    content = Path("core/orchestrator.py").read_text(encoding="utf-8")

    assert "from skills.base import SkillRequest" in content
    assert "from skills.router import skill_router" in content
    assert "_run_skill_preflight" in content
    assert "=== Skill Destekleri ===" in content


def test_startup_routers_contains_skills_router_contract():
    content = Path("startup/routers.py").read_text(encoding="utf-8")

    assert "from api.skills_router import router as skills_router" in content
    assert "app.include_router(skills_router" in content
