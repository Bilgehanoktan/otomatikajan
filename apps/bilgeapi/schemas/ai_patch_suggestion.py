from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, ConfigDict


class AIPatchSuggestionRequest(BaseModel):
    feedback_id: Optional[str] = None
    revision_id: Optional[str] = None
    instruction: str = Field(..., min_length=1)


class AIPatchSuggestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    pr_draft_id: str
    feedback_id: Optional[str] = None
    revision_id: Optional[str] = None
    provider: str
    model_name: Optional[str] = None
    prompt_hash: str
    context_summary: Optional[Dict[str, Any]] = None
    suggested_patch_code: str
    rationale: Optional[str] = None
    risk_notes: Optional[str] = None
    risk_level: str
    verification_id: Optional[str] = None
    status: str
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime



class AIPatchSuggestionDecisionRequest(BaseModel):
    reason: Optional[str] = None


class AIPatchSuggestionDecisionResponse(BaseModel):
    id: str
    status: str
    reason: Optional[str] = None
    updated_at: datetime
