from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import UTC, datetime
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class TaskArtifact:
    artifact_id: str
    step_id: str
    path: str
    artifact_type: str
    sha256: str
    created_at: str = field(default_factory=utc_now_iso)


@dataclass
class GateDecision:
    gate_id: str
    decision: str
    risk_score: float
    reason: str
    required_approval: str | None = None


@dataclass
class TaskFlowEvent:
    event_name: str
    workflow_id: str
    step_id: str | None = None
    incident_id: str = ""
    trace_id: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)


@dataclass
class TaskStep:
    step_id: str
    step_type: str
    handler: str
    status: str = "PENDING"
    retry: int = 0
    timeout_seconds: int | None = None
    condition: str | None = None
    always_run: bool = False
    attempts: int = 0
    started_at: str | None = None
    finished_at: str | None = None
    error: str | None = None
    artifacts: list[TaskArtifact] = field(default_factory=list)


@dataclass
class WorkflowRun:
    workflow_id: str
    workflow_name: str
    incident_id: str
    trace_id: str
    status: str = "CREATED"
    current_step: str | None = None
    started_at: str = field(default_factory=utc_now_iso)
    finished_at: str | None = None
    risk_score: float = 0.0
    final_decision: str | None = None
    steps: list[TaskStep] = field(default_factory=list)
    artifacts: list[TaskArtifact] = field(default_factory=list)
    events: list[TaskFlowEvent] = field(default_factory=list)


def to_plain_data(value: Any) -> Any:
    if is_dataclass(value):
        return {key: to_plain_data(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {key: to_plain_data(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_plain_data(item) for item in value]
    return value

