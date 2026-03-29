from types import SimpleNamespace

import pytest

from core.sandbox_runner import SandboxRunner
from core.repair_orchestrator import RepairOrchestrator


@pytest.mark.asyncio
async def test_sandbox_should_block_execution_in_production_when_docker_unavailable(monkeypatch):
    """
    Production'da Docker yoksa subprocess fallback'a düşmemeli;
    security_blocked dönmeli.
    """
    monkeypatch.setenv("APP_ENV", "production")

    runner = SandboxRunner(use_docker=False)

    async def _docker_unavailable():
        return False

    monkeypatch.setattr(runner, "_docker_available_check", _docker_unavailable)

    result = await runner.run_python("print('hello')")

    assert result.success is False
    assert result.mode == "security_blocked"
    assert result.blocked_reason == "docker_not_running_prod"


@pytest.mark.asyncio
async def test_sandbox_should_use_hardened_docker_flags_for_ruff(monkeypatch):
    """
    Ruff docker komutunda güvenlik flag'leri bulunmalı.
    """
    runner = SandboxRunner(use_docker=True)

    async def _docker_available():
        return True

    captured = {}

    class DummyProc:
        returncode = 0

        async def communicate(self):
            return (b"OK", b"")

    async def _fake_exec(*cmd, **kwargs):
        captured["cmd"] = list(cmd)
        return DummyProc()

    monkeypatch.setattr(runner, "_docker_available_check", _docker_available)
    monkeypatch.setattr(
        "core.sandbox_runner.asyncio.create_subprocess_exec",
        _fake_exec,
        raising=True,
    )

    result = await runner.run_ruff_check("print('hello')")

    cmd = captured["cmd"]
    joined = " ".join(cmd)

    assert result.success is True
    assert "--network=none" in joined
    assert "--memory=128m" in joined
    assert "--cap-drop=ALL" in joined
    assert "--security-opt no-new-privileges" in joined
    assert "--read-only" in joined


@pytest.mark.asyncio
async def test_repair_orchestrator_should_block_dangerous_diff():
    """
    os.system / DROP TABLE gibi tehlikeli diff'ler manuel review'e düşmeli.
    """
    orch = RepairOrchestrator()

    class MockJob:
        def __init__(self):
            self.job_id = "test-job"
            self.status = "pending"
        def transition(self, new_status, note=None):
            self.status = new_status
            return True

    job = MockJob()
    patch = SimpleNamespace(diff="import os\nos.system('rm -rf /')")

    result = await orch._step_architecture_guard(job, patch)

    assert result is False
