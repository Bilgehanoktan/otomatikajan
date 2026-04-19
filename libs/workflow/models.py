from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ERROR = "failed"
    SKIPPED = "skipped"
    WAITING = "waiting" # Waiting for dependencies or approval
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
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Optional[Dict[str, Any]] = None
    status: StepStatus = StepStatus.PENDING
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retries: int = 0
    max_retries: int = 3
    dependencies: List[str] = Field(default_factory=list)
    require_approval: bool = False
    input_schema: Optional[Dict[str, Any]] = None  # Deep validation support (Draft-07 JSON Schema likely)
    compensation_action: Optional[str] = None      # Logic to run if this step needs to be 'undone'
    is_compensated: bool = False                  # Flag for audit/compliance

class WorkflowInstance(BaseModel):
    id: str
    workflow_type: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    steps: List[WorkflowStep] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    review_required: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
