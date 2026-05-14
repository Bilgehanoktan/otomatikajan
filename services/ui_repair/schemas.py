from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

class BaseSchema(BaseModel):
    model_config = {"from_attributes": True}

class UIRepairOverview(BaseSchema):
    ui_health_score: float
    total_routes: int
    passing_routes: int
    failing_routes: int
    open_cases: int
    critical_cases: int
    last_smoke_run_at: Optional[datetime] = None
    last_smoke_status: Optional[str] = None
    top_failure_types: List[Dict[str, Any]]

class UIRouteHealthSchema(BaseSchema):
    route: str
    status: str
    http_status: Optional[int]
    blank_page_detected: bool
    console_error_count: int
    network_error_count: int
    last_checked_at: Optional[datetime]
    last_case_id: Optional[UUID]

class UIRepairCaseSchema(BaseSchema):
    id: UUID
    route: str
    status: str
    severity: str
    failure_type: str
    title: Optional[str]
    summary: Optional[str] = None
    console_errors: List[Any] = []
    network_errors: List[Any] = []
    screenshot_path: Optional[str] = None
    trace_path: Optional[str] = None
    evidence_json: Dict[str, Any] = {}
    linked_incident_id: Optional[UUID] = None
    linked_runtime_diagnostic_id: Optional[str] = None
    next_recommended_action: str = "READY_FOR_STAGEHAND"
    patch_path: Optional[str] = None
    pr_url: Optional[str] = None
    repair_summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class UIRepairAttemptSchema(BaseSchema):
    id: UUID
    case_id: UUID
    attempt_no: int
    status: str
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    stagehand_status: Optional[str]
    open_swe_status: Optional[str]
    diagnostic_brief: Optional[Dict[str, Any]] = Field(alias="diagnostic_brief_json")
    suspected_files: List[str] = Field(alias="suspected_files_json")
    repair_instruction: Optional[str]
    patch_path: Optional[str]
    patch_summary: Optional[str]
    pr_url: Optional[str]
    error_message: Optional[str]
    created_at: datetime

class UIRepairEventSchema(BaseSchema):
    id: UUID
    case_id: UUID
    attempt_id: Optional[UUID]
    event_type: str
    status: Optional[str]
    message: str
    payload: Dict[str, Any] = Field(alias="payload_json")
    created_at: datetime

class UISmokeRunSchema(BaseSchema):
    id: UUID
    status: str
    total_routes: int
    passed_routes: int
    failed_routes: int
    started_at: datetime
    finished_at: Optional[datetime]
    summary: Dict[str, Any]

class UIRepairPRReviewSchema(BaseSchema):
    id: UUID
    case_id: UUID
    attempt_id: UUID
    pr_url: Optional[str]
    status: str
    risk_level: str
    review_summary: Optional[str]
    describe_output: Dict[str, Any]
    review_output: Dict[str, Any]
    improve_output: Dict[str, Any]
    changed_files: List[str]
    finished_at: Optional[datetime]
    created_at: datetime

class UIRepairVerifierRunSchema(BaseSchema):
    id: UUID
    case_id: UUID
    attempt_id: UUID
    pr_url: Optional[str]
    status: str
    lint_status: Optional[str]
    typecheck_status: Optional[str]
    build_status: Optional[str]
    unit_test_status: Optional[str]
    playwright_status: Optional[str]
    smoke_status: Optional[str]
    route_regression_status: Optional[str]
    result_summary: Dict[str, Any]
    finished_at: Optional[datetime]
    created_at: datetime

class UIRepairGovernanceApprovalSchema(BaseSchema):
    id: UUID
    case_id: UUID
    attempt_id: UUID
    pr_url: Optional[str]
    approval_request_id: Optional[str]
    status: str
    risk_level: Optional[str]
    auto_apply_allowed: bool
    requires_operator_approval: bool
    policy_decision: Dict[str, Any]
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    rejected_by: Optional[str]
    rejected_at: Optional[datetime]
    rejection_reason: Optional[str]
    created_at: datetime

class UIRepairApplyResultSchema(BaseSchema):
    id: UUID
    case_id: UUID
    attempt_id: UUID
    status: str
    apply_mode: Optional[str]
    merge_commit_sha: Optional[str]
    applied_at: Optional[datetime]
    applied_by: Optional[str]
    error_message: Optional[str]
    created_at: datetime

class UIMonitoringConfigSchema(BaseSchema):
    id: UUID
    enabled: bool
    interval_seconds: int
    route_scope: List[str] = Field(alias="route_scope_json")
    auto_repair_enabled: bool
    auto_repair_risk_threshold: str
    max_repairs_per_hour: int
    max_repairs_per_day: int
    cooldown_minutes: int
    notify_on_failure: bool
    notify_on_repair_started: bool
    notify_on_governance_waiting: bool
    updated_at: datetime

class UIMonitoringRunSchema(BaseSchema):
    id: UUID
    status: str
    triggered_by: str
    started_at: datetime
    finished_at: Optional[datetime]
    total_routes: int
    passed_routes: int
    failed_routes: int
    degraded_routes: int
    auto_repair_started_count: int
    cases_created_count: int
    cases_updated_count: int
    summary: Dict[str, Any] = Field(alias="summary_json")
    created_at: datetime

class UIRouteHealthHistSchema(BaseSchema):
    id: UUID
    route: str
    status: str
    http_status: int
    response_time_ms: float
    captured_at: datetime

class UIChaosDrillScenarioSchema(BaseSchema):
    id: UUID
    name: str
    description: Optional[str]
    failure_type: str
    target_route: Optional[str]
    target_component: Optional[str]
    target_api: Optional[str]
    expected_detection: Optional[str]
    expected_severity: Optional[str]
    is_enabled: bool
    is_destructive: bool
    requires_sandbox: bool

class UIChaosDrillRunSchema(BaseSchema):
    id: UUID
    scenario_id: UUID
    status: str
    started_at: datetime
    finished_at: Optional[datetime]
    target_route: Optional[str]
    injected_failure_type: str
    detection_status: Optional[str]
    passed: bool
    created_at: datetime

class UISoakValidationRunSchema(BaseSchema):
    id: UUID
    status: str
    started_at: datetime
    finished_at: Optional[datetime]
    duration_minutes: int
    monitoring_runs_count: int
    total_failures_detected: int
    created_at: datetime

class UIRecoveryProofPackSchema(BaseSchema):
    id: UUID
    pack_name: str
    status: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    evidence_hash: str
    executive_summary: str
    created_at: datetime

# --- Phase 9: Advanced Chaos & Escalation Schemas ---

class UIAdvancedChaosScenarioSchema(BaseSchema):
    id: UUID
    name: str
    description: Optional[str]
    chaos_type: str
    target_route: Optional[str]
    target_api: Optional[str]
    target_resource: Optional[str]
    injection_mode: str
    expected_detection: Optional[str]
    expected_severity: Optional[str]
    requires_sandbox: bool
    is_destructive: bool
    max_duration_seconds: int
    is_enabled: bool
    created_at: datetime
    updated_at: datetime

class UIAdvancedChaosRunSchema(BaseSchema):
    id: UUID
    scenario_id: Optional[UUID]
    status: str
    chaos_type: Optional[str]
    target_route: Optional[str]
    started_at: datetime
    finished_at: Optional[datetime]
    duration_seconds: Optional[int]
    injected_latency_ms: int
    injected_timeout_ms: int
    blocked_resource_pattern: Optional[str]
    websocket_disconnected: bool
    cache_stale: bool
    detected_by_monitoring: bool
    detected_failure_type: Optional[str]
    detected_severity: Optional[str]
    policy_decision: Optional[str]
    repair_case_id: Optional[UUID]
    operational_incident_id: Optional[UUID]
    evidence_path: Optional[str]
    cleanup_status: str
    passed: bool
    failure_reason: Optional[str]
    summary_json: Dict[str, Any]
    created_at: datetime

class UIOperatorEscalationSchema(BaseSchema):
    id: UUID
    source_type: Optional[str]
    source_id: Optional[UUID]
    route: Optional[str]
    severity: str
    escalation_level: int
    status: str
    reason: Optional[str]
    assigned_to: Optional[str]
    notification_channels_json: List[str]
    notification_status_json: Dict[str, str]
    acknowledged_by: Optional[str]
    acknowledged_at: Optional[datetime]
    resolved_by: Optional[str]
    resolved_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

class UINotificationDeliverySchema(BaseSchema):
    id: UUID
    escalation_id: UUID
    channel: str
    status: str
    recipient: str
    title: str
    message_summary: Optional[str]
    provider_response_json: Dict[str, Any]
    sent_at: Optional[datetime]
    failed_at: Optional[datetime]
    error_message: Optional[str]
    created_at: datetime

class UICrisisControlStateSchema(BaseSchema):
    id: UUID
    mode: str
    self_healing_frozen: bool
    monitoring_frozen: bool
    auto_repair_frozen: bool
    reason: Optional[str]
    activated_by: Optional[str]
    activated_at: datetime
    deactivated_by: Optional[str]
    deactivated_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

# --- Phase 10: Final Enterprise Readiness & Release Gate Schemas ---

class UIRedTeamScenarioSchema(BaseSchema):
    id: UUID
    name: str
    description: Optional[str]
    risk_type: str
    expected_detection: Optional[str]
    expected_severity: Optional[str]
    expected_policy_decision: Optional[str]
    is_destructive: bool
    created_at: datetime

class UIRedTeamRunSchema(BaseSchema):
    id: UUID
    scenario_id: UUID
    status: str
    actual_detection: Optional[str]
    actual_severity: Optional[str]
    actual_decision: Optional[str]
    passed: bool
    vulnerability_found: bool
    findings_json: Dict[str, Any]
    started_at: datetime
    finished_at: Optional[datetime]

class UIEnterpriseReadinessAssessmentSchema(BaseSchema):
    id: UUID
    overall_score: float
    rating: str
    monitoring_score: float
    governance_score: float
    resilience_score: float
    audit_score: float
    operations_score: float
    assessment_json: Dict[str, Any]
    blocker_list_json: List[str]
    warning_list_json: List[str]
    assessed_by: Optional[str]
    created_at: datetime

class UIReleaseGateDecisionSchema(BaseSchema):
    id: UUID
    assessment_id: UUID
    decision: str
    rationale: Optional[str]
    gate_conditions_json: Dict[str, Any]
    approver: Optional[str]
    decided_at: datetime

class UIFinalAuditPackSchema(BaseSchema):
    id: UUID
    name: str
    version: str
    summary_report_path: Optional[str]
    evidence_bundle_hash: Optional[str]
    content_manifest_json: Dict[str, Any]
    is_sealed: bool
    created_at: datetime

class UIOperatorHandoverReportSchema(BaseSchema):
    id: UUID
    title: str
    architecture_summary: Optional[str]
    operational_guide: Optional[str]
    emergency_protocols: Optional[str]
    residual_risks_json: List[str]
    limitations_json: List[str]
    report_path: Optional[str]
    created_at: datetime
