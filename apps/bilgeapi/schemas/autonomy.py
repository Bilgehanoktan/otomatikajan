from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class AutonomyDecisionRequest(BaseModel):
    incident_id: str = Field(..., description="ID of the incident to evaluate")
    action_type: Optional[str] = Field(None, description="Proposed action type to evaluate eligibility for")

class AutonomyDecisionResponse(BaseModel):
    decision_id: str = Field(..., description="Unique ID of the decision log")
    incident_id: str = Field(..., description="Incident ID evaluated")
    correlation_id: str = Field(..., description="Correlation ID from the incident")
    classification: str = Field(..., description="Classified incident kind/anomaly category")
    risk_score: float = Field(..., description="Computed risk score (0.0 to 100.0)")
    risk_level: str = Field(..., description="Computed risk level (LOW, MEDIUM, HIGH, CRITICAL)")
    active_autonomy_mode: str = Field(..., description="Active autonomy mode setting at calculation time")
    eligibility: str = Field(..., description="Eligibility decision (AUTO_RUN, WARNING_OPERATOR_REVIEW, HUMAN_GATE_REQUIRED, BLOCKED)")
    requires_human_gate: bool = Field(..., description="Whether a human gate validation is required")
    human_gate_type: Optional[str] = Field(None, description="Type of human gate required (e.g. remediation_approval)")
    action_type: Optional[str] = Field(None, description="Action type evaluated")
    decision_reason: str = Field(..., description="Detailed explanation of the decision logic")
    created_at: datetime = Field(..., description="Decision timestamp")

    model_config = {


        "from_attributes": True


    }


class ManagementGateUpdateRequest(BaseModel):
    unlocked: bool = Field(..., description="Whether operator management actions are unlocked")
    reason: Optional[str] = Field(None, max_length=240, description="Operator reason shown in audit/UI context")


class ManagementGateResponse(BaseModel):
    unlocked: bool = Field(..., description="Whether operator management actions are currently unlocked")
    status: str = Field(..., description="LOCKED or UNLOCKED")
    reason: Optional[str] = Field(None, description="Operator reason for the latest transition")
    forbidden_actions: List[str] = Field(..., description="Actions that remain forbidden even when the gate is unlocked")
    human_gate_required: bool = Field(..., description="Whether human gate enforcement remains active")
    updated_by: Optional[str] = Field(None, description="Identity that changed the gate in this response")
