from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict


class ResearchCreate(BaseModel):
    incident_id: str = Field(..., description="ID of the associated incident")
    query: str = Field(..., description="Search query for research")


class ResearchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    incident_id: str
    query: str
    status: str
    error_message: Optional[str] = None
    tenant_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class EvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    research_id: str
    source_url: str
    source_domain: str
    title: Optional[str] = None
    snippet: Optional[str] = None
    raw_content_summary: Optional[str] = None
    content_hash: str
    trust_score: float
    retrieved_at: datetime


class ProposalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    research_id: str
    title: str
    rationale: str
    patch_code: str
    risk_analysis: Optional[Dict[str, Any]] = None
    gate_status: str
    gate_score: Optional[float] = None
    approval_status: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    ready_for_human_apply: bool
    created_at: datetime
    updated_at: datetime



class DraftPrResponse(BaseModel):
    patch_code: str
    title: str
    description: str
    risk_level: str
    affected_files: List[str]
    potential_side_effects: str
    mitigation_plan: str
