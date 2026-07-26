import pytest
from unittest.mock import MagicMock
from bilgeapi.services.skill_registry import SkillRegistryService
from bilgeapi.services.skill_check_service import SkillCheckService
from bilgeapi.schemas.skills import SkillMetadataResponse

@pytest.fixture
def mock_registry():
    registry = MagicMock(spec=SkillRegistryService)
    registry.initialized = True
    
    skills_db = {
        "bilgeapi-repair-request-safety": SkillMetadataResponse(
            name="bilgeapi-repair-request-safety", source="bilgeapi-custom", version="1.0.0",
            license="MIT", risk_level="high_value_policy", hash="h1", enabled=True
        ),
        "bilgeapi-pr-verification-gate": SkillMetadataResponse(
            name="bilgeapi-pr-verification-gate", source="bilgeapi-custom", version="1.0.0",
            license="MIT", risk_level="high_value_policy", hash="h2", enabled=True
        ),
        "bilgeapi-self-healing-policy": SkillMetadataResponse(
            name="bilgeapi-self-healing-policy", source="bilgeapi-custom", version="1.0.0",
            license="MIT", risk_level="high_value_policy", hash="h3", enabled=True
        ),
        "bilgeapi-skill-integrity": SkillMetadataResponse(
            name="bilgeapi-skill-integrity", source="bilgeapi-custom", version="1.0.0",
            license="MIT", risk_level="high_value_policy", hash="h4", enabled=True
        ),
        "security-and-hardening": SkillMetadataResponse(
            name="security-and-hardening", source="external-vendor", version="1.0.0",
            license="MIT", risk_level="low", hash="h5", enabled=True
        )
    }
    
    registry.get_skill.side_effect = lambda name: skills_db[name] if name in skills_db else ValueError("Not found")
    return registry

@pytest.mark.asyncio
async def test_safe_python_patch_passes(mock_registry):
    checker = SkillCheckService(registry=mock_registry)
    patch = "def safe_func():\n    return 42"
    res = await checker.check_patch("pr", "pr_1", ["bilgeapi-repair-request-safety"], patch, tenant_id="tenant-a")
    assert res.passed is True
    assert res.status == "PASS"

@pytest.mark.asyncio
async def test_syntax_invalid_python_blocked(mock_registry):
    checker = SkillCheckService(registry=mock_registry)
    patch = "def unsafe_func(\n    return 42"
    res = await checker.check_patch("pr", "pr_2", ["bilgeapi-repair-request-safety"], patch, tenant_id="tenant-a")
    assert res.passed is False
    assert res.status == "BLOCKED"
    assert any("syntax error" in r.lower() for r in res.checks[0].reason.split("; "))

@pytest.mark.asyncio
async def test_comments_containing_dangerous_words_do_not_false_positive(mock_registry):
    checker = SkillCheckService(registry=mock_registry)
    patch = "# This is a comment mentioning eval and subprocess\ndef safe_func():\n    pass"
    res = await checker.check_patch("pr", "pr_3", ["bilgeapi-repair-request-safety"], patch, tenant_id="tenant-a")
    assert res.passed is True
    assert res.status == "PASS"

@pytest.mark.asyncio
async def test_dangerous_constructs_blocked(mock_registry):
    checker = SkillCheckService(registry=mock_registry)
    dangerous_patches = [
        "eval('1+1')",
        "exec('print(1)')",
        "import os",
        "import sys",
        "import subprocess",
        "os.system('ls')",
        "subprocess.run(['ls'])",
        "__import__('os')",
        "getattr(builtins, 'eval')",
        "open('test.txt', 'w')"
    ]
    for p in dangerous_patches:
        res = await checker.check_patch("pr", "pr_4", ["bilgeapi-repair-request-safety"], p, tenant_id="tenant-a")
        assert res.passed is False
        assert res.status == "BLOCKED"

@pytest.mark.asyncio
async def test_string_concatenation_evasion_blocked(mock_registry):
    checker = SkillCheckService(registry=mock_registry)
    evasion_patches = [
        "getattr(builtins, 'ev' + 'al')",
        "getattr(__builtins__, 'ex' + 'ec')",
        "getattr(x, 'sub' + 'process')"
    ]
    for p in evasion_patches:
        res = await checker.check_patch("pr", "pr_5", ["bilgeapi-repair-request-safety"], p, tenant_id="tenant-a")
        assert res.passed is False
        assert res.status == "BLOCKED"

@pytest.mark.asyncio
async def test_non_python_regex_fallback_with_word_boundaries(mock_registry):
    checker = SkillCheckService(registry=mock_registry)
    
    # Non-python patch with eval word should be blocked
    non_py_blocked = "eval some text"
    res = await checker.check_patch("pr", "pr_6", ["bilgeapi-repair-request-safety"], non_py_blocked, tenant_id="tenant-a")
    assert res.passed is False
    assert res.status == "BLOCKED"
    
    # Non-python patch with substring of eval but not word should pass
    non_py_passed = "evaluation text"
    res = await checker.check_patch("pr", "pr_7", ["bilgeapi-repair-request-safety"], non_py_passed, tenant_id="tenant-a")
    assert res.passed is True
    assert res.status == "PASS"

@pytest.mark.asyncio
async def test_missing_tenant_context_fails_closed(mock_registry):
    checker = SkillCheckService(registry=mock_registry)
    with pytest.raises(ValueError, match="tenant_id is required"):
        await checker.check_patch("pr", "pr_8", ["bilgeapi-repair-request-safety"], "print(1)")
