from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class PrVerificationResponse(BaseModel):
    id: str
    pr_draft_id: str
    proposal_id: str
    revision_id: Optional[str] = None
    status: str
    review_score: float
    review_decision: str
    risk_level: str
    risk_flags: Optional[List[str]] = None
    affected_files: Optional[List[str]] = None
    mutation_detected: bool
    test_files_present: bool
    patch_size_lines: int
    test_plan: Optional[List[str]] = None
    rollback_plan: Optional[str] = None
    verification_report: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PrReviewReportResponse(BaseModel):
    pr_draft_id: str
    proposal_id: str
    review_score: float
    review_decision: str
    risk_level: str
    report_markdown: str
    created_at: datetime
