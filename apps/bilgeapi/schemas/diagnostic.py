from datetime import datetime
from enum import Enum
from typing import List, Any, Optional
from pydantic import BaseModel, Field

class DiagnosticStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class DiagnosticStartResponse(BaseModel):
    diagnostic_id: str
    status: DiagnosticStatus = DiagnosticStatus.QUEUED
    next_action: str = "CHECK_DIAGNOSTIC_STATUS"

class DiagnosticResult(BaseModel):
    diagnostic_id: str
    incident_id: str
    status: DiagnosticStatus
    summary: Optional[str] = None
    root_cause_hypothesis: Optional[str] = None
    confidence: Optional[float] = None
    risk_score: Optional[float] = None
    findings: List[Any] = Field(default_factory=list)
    recommendations: List[Any] = Field(default_factory=list)
    created_at: datetime
    completed_at: Optional[datetime] = None
