from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class RemediationRunbookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    action_type: str
    severity_allowed: str
    requires_human_gate: bool
    enabled: bool
    execution_mode: str
    max_attempts: int
    cooldown_seconds: int
    safety_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class RemediationAttemptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    finding_id: str
    runbook_id: Optional[str] = None
    action_type: str
    status: str
    attempt_no: int
    before_health: Optional[Dict[str, Any]] = None
    after_health: Optional[Dict[str, Any]] = None
    output_summary: Optional[str] = None
    error_message: Optional[str] = None
    policy_decision: Optional[Dict[str, Any]] = None
    forbidden_actions_checked: Optional[List[str]] = None
    ledger_chain_id: Optional[str] = None
    created_by: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime



class RunbookEnableDisableRequest(BaseModel):
    pass


class EmergencyRecoveryRequest(BaseModel):
    finding_id: str
    action_type: str


class FindingIntakeRequest(BaseModel):
    source_type: str
    source_id: str
    title: str
    description: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    evidence_summary: Optional[Dict[str, Any]] = None
    recommended_action: Optional[str] = None
    tenant_id: Optional[str] = None


class RecoveryEventReport(BaseModel):
    event_type: str
    timestamp: str
    service_name: str
    attempt_no: int
    output: Optional[str] = None
    error: Optional[str] = None
    status: str


class ExternalRecoveryReportRequest(BaseModel):
    events: List[RecoveryEventReport]


