from pathlib import Path

import pytest

from packages.skills.base import SkillRequest
from packages.skills.adapters.vault_memory_adapter import VaultMemorySkillAdapter


@pytest.mark.asyncio
async def test_vault_memory_adapter_writes_markdown_note(tmp_path: Path):
    adapter = VaultMemorySkillAdapter()
    adapter.vault_root = tmp_path / "vault"
    adapter.vault_root.mkdir(parents=True, exist_ok=True)

    req = SkillRequest(
        task_type="subtask",
        title="Repair Router Bug",
        description="There is a bug in repair router.",
        project_id="p1",
        agent_id="backend_dev",
        context={"x": 1},
    )

    result = await adapter.execute(req)

    assert result.success is True
    note_path = Path(result.data["path"])
    assert note_path.exists()

    content = note_path.read_text(encoding="utf-8")
    assert "# Repair Router Bug" in content
    assert "project_id: p1" in content
    assert "agent_id: backend_dev" in content
    assert "task_type: subtask" in content


@pytest.mark.asyncio
async def test_vault_memory_adapter_slugify_is_safe(tmp_path: Path):
    adapter = VaultMemorySkillAdapter()
    adapter.vault_root = tmp_path / "vault"
    adapter.vault_root.mkdir(parents=True, exist_ok=True)

    req = SkillRequest(
        task_type="generic",
        title=r"repair/router\bug fix",
        description="desc",
    )

    result = await adapter.execute(req)

    note_path = Path(result.data["path"])
    assert note_path.exists()
    assert "/" not in note_path.name
    assert "\\" not in note_path.name


@pytest.mark.asyncio
async def test_vault_memory_adapter_supports_turkish_characters(tmp_path: Path):
    adapter = VaultMemorySkillAdapter()
    adapter.vault_root = tmp_path / "vault"
    adapter.vault_root.mkdir(parents=True, exist_ok=True)

    req = SkillRequest(
        task_type="generic",
        title="İyileştirme Hata Çözümü Şablonu",
        description="Türkçe içerik",
    )

    result = await adapter.execute(req)

    assert result.success is True
    note_path = Path(result.data["path"])
    assert note_path.exists()
    assert note_path.name.endswith(".md")
