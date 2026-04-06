from packages.packages.skills.registry import skill_registry


def test_skill_registry_contains_expected_skills():
    ids = skill_registry.ids()

    assert "optimization" in ids
    assert "debugging" in ids
    assert "file_search" in ids
    assert "vault_memory" in ids
    assert "skill_creator" in ids


def test_skill_registry_get_returns_adapter():
    skill = skill_registry.get("optimization")
    assert skill is not None
    assert getattr(skill, "skill_id", None) == "optimization"
