from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    WAITING = "waiting" # Waiting for dependencies or approval
    REPLAY_PENDING = "replay_pending"

class WorkflowStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    REPLAYING = "REPLAYING"
    PAUSED = "PAUSED"

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
