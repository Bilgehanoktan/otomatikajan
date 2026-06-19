from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator
import re

class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class IncidentCreate(BaseModel):
    project_key: str
    source_system: str
    environment: str
    kind: str
    severity: Severity
    error_message: str = Field(..., min_length=1)
    stack_trace: Optional[str] = None
    occurred_at: datetime
    correlation_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("project_key")
    @classmethod
    def validate_project_key(cls, v: str) -> str:
        if not re.match(r"^[a-z0-9\-]+$", v):
            raise ValueError("project_key must be lowercase alphanumeric and dashes only")
        return v

    @field_validator("error_message")
    @classmethod
    def validate_error_message(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("error_message cannot be empty or whitespace only")
        return v

class IncidentResponse(IncidentCreate):
    id: str
    created_at: datetime
