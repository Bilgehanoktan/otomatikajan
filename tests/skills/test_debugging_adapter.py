from types import SimpleNamespace

import pytest

from packages.skills.base import SkillRequest
from packages.skills.adapters.debugging_adapter import DebuggingSkillAdapter


class _FakeRepairOrchestrator:
    def __init__(self):
        self.called_with = None

    async def start_repair(self, incident):
        self.called_with = incident
        return SimpleNamespace(job_id="r-123", status="queued")


@pytest.mark.asyncio
async def test_debugging_adapter_starts_repair_pipeline(monkeypatch):
    adapter = DebuggingSkillAdapter()
    fake = _FakeRepairOrchestrator()

    monkeypatch.setattr(
        "core.repair_orchestrator.get_repair_orchestrator",
        lambda *args, **kwargs: fake,
    )

    req = SkillRequest(
        task_type="generic",
        title="repair router traceback bug",
        description="traceback in orchestrator and repair flow",
        project_id="p-42",
        context={"stack": "Traceback..."},
    )

    result = await adapter.execute(req)

    assert result.success is True
    assert result.data["repair_job_id"] == "r-123"
    assert result.data["status"] == "queued"
    assert fake.called_with is not None
    assert hasattr(fake.called_with, "symptom")
    assert "traceback" in fake.called_with.symptom.lower()


def test_debugging_adapter_can_handle_bug_text():
    adapter = DebuggingSkillAdapter()

    req = SkillRequest(
        task_type="generic",
        title="traceback in orchestrator",
        description="error and failure in worker",
    )

    assert adapter.can_handle(req) is True


def test_debugging_adapter_does_not_handle_ui_task():
    adapter = DebuggingSkillAdapter()

    req = SkillRequest(
        task_type="generic",
        title="improve dashboard spacing",
        description="make card spacing better",
    )

    assert adapter.can_handle(req) is False
