from __future__ import annotations

from typing import Any

from services.taskflow.taskflow_models import TaskFlowEvent


WORKFLOW_STARTED = "taskflow.workflow.started"
STEP_STARTED = "taskflow.step.started"
STEP_SUCCEEDED = "taskflow.step.succeeded"
STEP_FAILED = "taskflow.step.failed"
STEP_BLOCKED = "taskflow.step.blocked"
GATE_WAITING = "taskflow.gate.waiting"
WORKFLOW_COMPLETED = "taskflow.workflow.completed"


def create_event(
    event_name: str,
    *,
    workflow_id: str,
    step_id: str | None = None,
    incident_id: str = "",
    trace_id: str = "",
    payload: dict[str, Any] | None = None,
) -> TaskFlowEvent:
    return TaskFlowEvent(
        event_name=event_name,
        workflow_id=workflow_id,
        step_id=step_id,
        incident_id=incident_id,
        trace_id=trace_id,
        payload=payload or {},
    )

