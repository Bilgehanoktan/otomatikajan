import pytest
from packages.skills.adapters.vault_memory_adapter import VaultMemorySkillAdapter
from packages.skills.adapters.debugging_adapter import DebuggingSkillAdapter
from packages.skills.adapters.skill_creator_adapter import SkillCreatorSkillAdapter
from packages.skills.base import SkillRequest
from unittest.mock import MagicMock, patch, AsyncMock
from packages.repair_engine.schemas.incident import IncidentSource, IncidentSeverity

def test_vlt_extreme_slugification():
    """VLT-01 — Vault slugification extreme karakterleri temizliyor"""
    adapter = VaultMemorySkillAdapter()
    titles = [
        "Task with / and \\",
        "!!! Special @#$% Characters ???",
        "Multiple---Dashes",
        "Trailing dash-",
        "---Leading dash"
    ]
    for t in titles:
        slug = adapter._slugify(t)
        assert "/" not in slug
        assert "\\" not in slug
        assert "@" not in slug
        assert not slug.startswith("-")
        assert not slug.endswith("-")

@pytest.mark.asyncio
async def test_dbg_enum_strictness():
    """DBG-01 — Debugging adapter ENUM değerlerini doğru kullanıyor"""
    adapter = DebuggingSkillAdapter()
    req = SkillRequest(
        task_type="bug",
        title="Crash",
        description="Segfault in worker",
        project_id="p-123"
    )
    
    with patch("core.repair_orchestrator.RepairOrchestrator.start_repair", new_callable=AsyncMock) as mock_trigger:
        await adapter.execute(req)
        assert mock_trigger.called
        # Verify IncidentRecord fields
        incident = mock_trigger.call_args[0][0]
        assert incident.source == IncidentSource.MANUAL
        assert incident.severity == IncidentSeverity.MEDIUM

@pytest.mark.asyncio
async def test_scr_manifest_validation(tmp_path):
    """SCR-01 — Skill Creator geçerli manifest ve kod üretiyor"""
    from pathlib import Path
    # Override generated_skills_dir for testing
    adapter = SkillCreatorSkillAdapter()
    adapter.generated_dir = Path(tmp_path)
    
    req = SkillRequest(
        task_type="create_skill",
        title="Custom Analytics",
        description="Skill to analyze traffic",
        context={"skill_id": "analytics_v1"}
    )
    
    res = await adapter.execute(req)
    assert res.success

    # Check files (folder name should be analytics_v1)
    root = tmp_path / "analytics_v1"
    assert root.exists()
    assert (root / "SKILL.md").exists()
    assert (root / "manifest.json").exists()
    
    import json
    manifest = json.loads((root / "manifest.json").read_text())
    assert manifest["id"] == "analytics_v1"
    assert manifest["name"] == "Custom Analytics"
