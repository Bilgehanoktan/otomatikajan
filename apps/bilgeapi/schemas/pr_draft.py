from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class PrDraftRiskSummary(BaseModel):
    risk_level: str = Field(..., description="Risk level (LOW, MEDIUM, HIGH)")
    risk_flags: List[str] = Field(default_factory=list, description="List of sensitive/risky files modified")


class PrDraftResponse(BaseModel):
    id: str
    proposal_id: str
    provider: str
    status: str
    github_pr_url: Optional[str] = None
    branch_name: Optional[str] = None
    title: str
    body: str
    evidence_hash: Optional[str] = None
    risk_level: str
    risk_flags: Optional[List[str]] = None
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
