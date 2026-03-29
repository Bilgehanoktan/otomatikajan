import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
from skills.adapters.optimization_adapter import OptimizationSkillAdapter
from skills.adapters.vault_memory_adapter import VaultMemorySkillAdapter
from skills.adapters.debugging_adapter import DebuggingSkillAdapter
from skills.adapters.skill_creator_adapter import SkillCreatorSkillAdapter
from skills.base import SkillRequest

@pytest.mark.asyncio
async def test_ut07_optimization_adapter_trims_context():
    """UT-07 — Optimization adapter description trim yapıyor"""
    adapter = OptimizationSkillAdapter()
    req = SkillRequest(
        task_type="generic",
        title="Big Task",
        description="A" * 5000,
        context={
            "memories": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "file_hits": ["f1", "f2", "f3", "f4", "f5", "f6"],
            "shared_context": "S" * 6000
        }
    )
    result = await adapter.execute(req)
    assert result.success is True
    assert len(result.data["description"]) == 2000
    assert len(result.data["memories"]) == 5
    assert len(result.data["file_hits"]) == 5
    assert len(result.data["shared_context"]) == 4000
    assert "description trimmed" in result.warnings[0]
    assert "shared_context trimmed" in result.warnings[1]

@pytest.mark.asyncio
async def test_ut08_optimization_adapter_handles_empty_context():
    """UT-08 — Optimization adapter boş context’te patlamıyor"""
    adapter = OptimizationSkillAdapter()
    req = SkillRequest(task_type="generic", title="Simple", description="Desc", context={})
    result = await adapter.execute(req)
    assert result.success is True
    assert result.data["memories"] == []
    assert result.data["file_hits"] == []

@pytest.mark.asyncio
async def test_ut09_vault_adapter_writes_note(tmp_path):
    """UT-09 — Vault adapter note yazıyor"""
    adapter = VaultMemorySkillAdapter()
    # Mock vault_root to use tmp_path
    adapter.vault_root = tmp_path
    
    req = SkillRequest(
        task_type="generic",
        title="Vault Test",
        description="Save this",
        project_id="p123",
        agent_id="a456"
    )
    result = await adapter.execute(req)
    assert result.success is True
    
    # Check if file exists
    files = list(tmp_path.glob("*.md"))
    assert len(files) == 1
    content = files[0].read_text()
    assert "project_id: p123" in content
    assert "agent_id: a456" in content
    assert "# Vault Test" in content

def test_ut10_vault_slugify_is_safe():
    """UT-10 — Vault slugify güvenli çalışıyor"""
    adapter = VaultMemorySkillAdapter()
    unsafe_title = "repair/router\\bug fix! @#$%^&*"
    slug = adapter._slugify(unsafe_title)
    
    assert "/" not in slug
    assert "\\" not in slug
    assert "@" not in slug
    assert " " not in slug
    # The current logic leaves trailing dashes from removed special characters
    assert slug.startswith("repair-router-bug-fix")

@pytest.mark.asyncio
async def test_ut11_ut12_skill_creator_creates_draft(tmp_path):
    """UT-11, UT-12 — Skill creator draft klasörü ve manifest oluşturuyor"""
    adapter = SkillCreatorSkillAdapter(generated_dir=str(tmp_path))
    
    req = SkillRequest(task_type="generic", title="New Work", description="Reusable logic", context={"skill_id": "repeat_v1"})
    result = await adapter.execute(req)

    assert result.success is True
    assert (tmp_path / "repeat_v1" / "SKILL.md").exists()
    assert (tmp_path / "repeat_v1" / "manifest.json").exists()

def test_ut13_debugging_adapter_can_handle():
    """UT-13 — Debugging adapter sadece ilgili task’ta handle ediyor"""
    adapter = DebuggingSkillAdapter()
    
    req_yes = SkillRequest(task_type="generic", title="fix error", description="traceback")
    assert adapter.can_handle(req_yes) is True
    
    req_no = SkillRequest(task_type="generic", title="ui spacing", description="colors")
    assert adapter.can_handle(req_no) is False

@pytest.mark.asyncio
async def test_ut14_debugging_adapter_calls_repair_orch():
    """UT-14 — Debugging adapter repair orchestrator’ı çağırıyor"""
    from repair.schemas.incident import IncidentSource
    adapter = DebuggingSkillAdapter()
    
    mock_orch = AsyncMock()
    mock_job = MagicMock()
    mock_job.job_id = "job-123"
    mock_job.status = "queued"
    mock_orch.start_repair.return_value = mock_job
    
    # Patching core.repair_orchestrator instead of the local import in the adapter
    with patch("core.repair_orchestrator.get_repair_orchestrator", return_value=mock_orch):
        req = SkillRequest(task_type="generic", title="Bug", description="Crash", project_id="p1")
        result = await adapter.execute(req)
        
        assert result.success is True
        assert result.data["repair_job_id"] == "job-123"
        mock_orch.start_repair.assert_called_once()
        incident = mock_orch.start_repair.call_args[0][0]
        assert incident.source == IncidentSource.MANUAL
        assert incident.incident_id == "inc-p1"
