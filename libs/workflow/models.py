from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ERROR = "failed"
    SKIPPED = "skipped"
    WAITING = "waiting" # Waiting for dependencies
    PENDING_APPROVAL = "pending_approval" # Waiting for manual review
    REPLAY_PENDING = "replay_pending"

class WorkflowStatus(str, Enum):
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ERROR = "ERROR"
    CANCELLED = "CANCELLED"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    REPLAYING = "REPLAYING"
    PAUSED = "PAUSED"
    PARTIAL_COMPLETE = "PARTIAL_COMPLETE"
    RETRYING = "RETRYING"

class ReplayMode(str, Enum):
    SAME_INPUT = "same_input"         # Just retry the step
    FROM_STEP = "from_step"           # Reset this step and all downstream
    WITH_OVERRIDE = "with_override"   # Replay with modified input/context

class WorkflowStep(BaseModel):
    id: str
    name: str
    action: str  # The function/path to call
    input_data: dict[str, Any] = Field(default_factory=dict)
    output_data: dict[str, Any] | None = None
    status: StepStatus = StepStatus.PENDING
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    retries: int = 0
    max_retries: int = 3
    dependencies: list[str] = Field(default_factory=list)
    require_approval: bool = False
    condition: str | None = None
    input_schema: dict[str, Any] | None = None  # Deep validation support (Draft-07 JSON Schema likely)
    compensation_action: str | None = None      # Logic to run if this step needs to be 'undone'
    is_compensated: bool = False                  # Flag for audit/compliance

class WorkflowInstance(BaseModel):
    id: str
    workflow_type: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    steps: list[WorkflowStep] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    review_required: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
