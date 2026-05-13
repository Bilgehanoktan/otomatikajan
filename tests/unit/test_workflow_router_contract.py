from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from services.workflow_api.router import (
    _is_active_workflow_status,
    _map_workflow,
    _workflow_template_step_count,
)


def _project(**overrides):
    values = {
        "id": uuid4(),
        "title": "test workflow",
        "workflow_template": "default",
        "status": "QUEUED",
        "source": "API",
        "execution_context": {},
        "report": "",
        "created_at": datetime(2026, 5, 12, tzinfo=timezone.utc),
        "started_at": None,
        "completed_at": None,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_empty_db_workflow_detail_exposes_planned_registry_steps():
    mapped = _map_workflow(_project(), [])

    assert mapped.status == "queued"
    assert [step.name for step in mapped.steps] == ["plan", "execute", "report"]
    assert [step.status for step in mapped.steps] == ["pending", "pending", "pending"]
    assert mapped.steps[1].dependencies == ["plan"]


def test_registry_step_count_matches_default_workflow_contract():
    assert _workflow_template_step_count("default") == 3
    assert _workflow_template_step_count("coding") == 3


def test_queued_workflow_is_active_for_control_plane_visibility():
    assert _is_active_workflow_status("queued") is True
    assert _is_active_workflow_status("waiting_approval") is True
    assert _is_active_workflow_status("completed") is False
