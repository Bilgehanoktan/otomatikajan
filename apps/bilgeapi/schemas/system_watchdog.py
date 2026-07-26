from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict


class SystemFindingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: Optional[str] = None
    source_type: str
    source_id: str
    source_hash: str
    title: str
    description: str
    severity: str
    risk_score: float
    status: str
    evidence_summary: Optional[Dict[str, Any]] = None
    recommended_action: Optional[str] = None
    human_gate_payload: Optional[Dict[str, Any]] = None
    occurrence_count: int
    first_seen_at: datetime
    last_seen_at: datetime
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    dismissed_by: Optional[str] = None
    dismissed_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    bilgeapi_research_id: Optional[str] = None
    bilgeapi_proposal_id: Optional[str] = None
    bilgeapi_pr_draft_id: Optional[str] = None
    bilgeapi_verification_id: Optional[str] = None
    bilgeapi_ledger_chain_id: Optional[str] = None
    created_by: Optional[str] = None
    correlation_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime



class WatchdogStatusResponse(BaseModel):
    enabled: bool
    status: str
    risk_threshold: int
    auto_finding: bool
    human_gate_required: bool
    open_findings: int = 0
    high_or_critical_findings: int = 0
    last_scan_correlation_id: Optional[str] = None


class WatchdogRunResponse(BaseModel):
    status: str
    enabled: bool
    correlation_id: str
    signals_seen: int
    findings_created: int
    findings_deduped: int
    findings: List[SystemFindingResponse] = Field(default_factory=list)
    forbidden_actions: List[str] = Field(default_factory=list)
    message: Optional[str] = None
