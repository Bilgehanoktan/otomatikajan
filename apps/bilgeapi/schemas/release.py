from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ReleaseCheckCreate(BaseModel):
    triggered_by: Optional[str] = Field(None, max_length=64)

class ReleaseCheckResponse(BaseModel):
    id: str
    status: str
    score: float
    blockers: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    checked_modules: Dict[str, str] = Field(default_factory=dict)
    checked_endpoints: Dict[str, str] = Field(default_factory=dict)
    smoke_trace: List[Dict[str, Any]] = Field(default_factory=list)
    app_version: Optional[str] = None
    git_sha: Optional[str] = None
    environment: Optional[str] = None
    triggered_by: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
