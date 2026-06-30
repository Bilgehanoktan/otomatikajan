import asyncio
import sqlite3

import pytest


async def dispose_workspace_engines():
    from apps.bilgeapi.memory.db import _engines

    for engine in list(_engines.values()):
        await engine.dispose()
    _engines.clear()

@pytest.mark.asyncio
async def test_initialize_workspace_state_creates_memory_schema(tmp_path, monkeypatch):
    from apps.bilgeapi import main as main_module
    from apps.bilgeapi.memory.db import _engines

    class FakeWorkspaceManager:
        def __init__(self):
            self.workspace_dir = tmp_path / ".bilgeapi"

        def initialize_workspace(self):
            (self.workspace_dir / "memory").mkdir(parents=True, exist_ok=True)
            return {".bilgeapi": str(self.workspace_dir)}

    monkeypatch.setattr(main_module, "WorkspaceManager", FakeWorkspaceManager)

    try:
        await main_module.initialize_workspace_state()
        db_file = tmp_path / ".bilgeapi" / "memory" / "bilgeapi.db"
        assert db_file.exists()
    finally:
        for engine in list(_engines.values()):
            await engine.dispose()
        _engines.clear()


@pytest.mark.asyncio
async def test_init_workspace_db_is_idempotent_under_concurrent_startup(tmp_path):
    from apps.bilgeapi.memory.db import _engines, init_workspace_db

    try:
        await asyncio.gather(*(init_workspace_db(tmp_path) for _ in range(4)))

        db_file = tmp_path / "memory" / "bilgeapi.db"
        with sqlite3.connect(db_file) as connection:
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }

        assert "workspace_approvals" in tables
        assert "workspace_audit_logs" in tables
    finally:
        for engine in list(_engines.values()):
            await engine.dispose()
        _engines.clear()
