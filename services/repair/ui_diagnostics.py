from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field

class UIDiagnosticRequest(BaseModel):
    route: str
    symptom: str
    expected_endpoint: str | None = None
    mode: str = "mock"

class UIDiagnosticNetworkError(BaseModel):
    url: str
    status: int
    method: str

class UIDiagnosticResult(BaseModel):
    diagnostic_id: str
    route: str
    symptom: str
    status: str
    network_errors: list[UIDiagnosticNetworkError] = Field(default_factory=list)
    console_errors: list[str] = Field(default_factory=list)
    dom_observations: list[str] = Field(default_factory=list)
    screenshot_ref: str | None = None
    suspected_root_cause: str
    suspected_files: list[str] = Field(default_factory=list)
    repair_instruction: str
    confidence_score: float
    created_at: str

class CEOFindingPayload(BaseModel):
    finding_id: str
    title: str
    description: str
    category: str = "ui_diagnostic"
    priority_score: int
    source_signal: str = "stagehand_diagnostic"
    affected_route: str
    affected_endpoint: str | None = None
    affected_files: list[str] = Field(default_factory=list)
    recommended_action: str
    recommended_agent: str = "swe_agent"
    requested_mode: str = "local_adapter"
    can_trigger_repair: bool = True
    status: str = "NEW"

class UIDiagnosticToFindingResult(BaseModel):
    status: str
    diagnostic_id: str
    artifact_ref: str
    finding: CEOFindingPayload
    next_step: str = "create_repair_case"
