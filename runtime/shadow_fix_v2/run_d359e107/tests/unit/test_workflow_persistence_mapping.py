from types import SimpleNamespace

from libs.db.models.core_models import ProjectStatus
from libs.workflow.models import StepStatus
from libs.workflow.persistence import _is_workflow_control_subtask, _step_status_from_db


def test_step_status_from_db_maps_error_to_failed():
    assert _step_status_from_db("ERROR") == StepStatus.FAILED
    assert _step_status_from_db("failed") == StepStatus.FAILED
    assert _step_status_from_db(ProjectStatus.COMPLETED) == StepStatus.COMPLETED


def test_workflow_control_filter_excludes_agent_telemetry_rows():
    assert _is_workflow_control_subtask(SimpleNamespace(action="plan_subtasks")) is True
    assert _is_workflow_control_subtask(SimpleNamespace(action="run_agent")) is False
