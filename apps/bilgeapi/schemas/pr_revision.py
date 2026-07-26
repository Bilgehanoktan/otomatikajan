from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class ReviewerFeedbackRequest(BaseModel):
    comment: str
    reviewer_id: str


class ReviewerFeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    pr_draft_id: str
    reviewer_id: str
    comment: str
    status: str
    created_at: datetime
    updated_at: datetime


class PatchRevisionRequest(BaseModel):
    feedback_id: Optional[str] = None
    revised_patch_code: str


class PatchRevisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    pr_draft_id: str
    feedback_id: Optional[str] = None
    revision_number: int
    revised_patch_code: str
    risk_analysis: Optional[Dict[str, Any]] = None
    risk_level: str
    verification_status: str
    created_by: str
    created_at: datetime
    updated_at: datetime

