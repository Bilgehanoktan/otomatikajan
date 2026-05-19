from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from uuid import UUID
from libs.db.models.ui_repair_models import (
    PatchAgentOpinionType, PatchNegotiationStatus,
    PatchDebateTurnType, PatchSelectionDecisionType
)

class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class UIGuardrailTuningProposalSchema(BaseSchema):
    id: UUID
    proposal_key: str
    source_type: str
    source_id: Optional[UUID]
    affected_guardrail: str
    affected_policy_key: str
    current_config: Dict[str, Any] = Field(alias="current_config_json")
    proposed_config: Dict[str, Any] = Field(alias="proposed_config_json")
    reason: str
    expected_security_gain: float
    expected_false_positive_impact: float
    expected_false_negative_impact: float
    risk_level: str
    status: str
    created_at: datetime
    updated_at: datetime

class UIDefensivePatternSchema(BaseSchema):
    id: UUID
    pattern_key: str
    source_finding_id: Optional[UUID]
    pattern_type: str
    affected_domain: str
    description: str
    detection_rule: Dict[str, Any] = Field(alias="detection_rule_json")
    mitigation_rule: Dict[str, Any] = Field(alias="mitigation_rule_json")
    confidence: float
    status: str
    created_at: datetime
    updated_at: datetime

class UIPolicyRegressionRunSchema(BaseSchema):
    id: UUID
    proposal_id: UUID
    status: str
    tested_events_count: int
    allowed_count: int
    denied_count: int
    false_allow_count: int
    false_block_count: int
    regression_score: float
    result_summary: Dict[str, Any] = Field(alias="result_summary_json")
    started_at: datetime
    finished_at: Optional[datetime]
    created_at: datetime

class UIGuardrailCanaryRunSchema(BaseSchema):
    id: UUID
    proposal_id: UUID
    status: str
    canary_scope: Dict[str, Any] = Field(alias="canary_scope_json")
    started_at: datetime
    finished_at: Optional[datetime]
    observed_events: int
    blocked_events: int
    unexpected_allows: int
    unexpected_blocks: int
    rollback_required: bool
    result_summary: Dict[str, Any] = Field(alias="result_summary_json")
    created_at: datetime

class UIDefenseOptimizationReportSchema(BaseSchema):
    id: UUID
    report_name: str
    period_start: datetime
    period_end: datetime
    total_proposals: int
    approved_proposals: int
    rejected_proposals: int
    security_score_before: float
    security_score_after: float
    false_allow_delta: int
    false_block_delta: int
    executive_summary: str
    evidence_hash: Optional[str]
    generated_at: datetime

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

# --- Phase 10 Red Team placeholders removed in favor of Phase 24 consolidation ---


# --- Phase 10 Red Team runs removed in favor of Phase 24 operations ---


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

# Phase 11 Pilot Rollout Schemas

class UIPilotRolloutBase(BaseSchema):
    name: str
    mode: str = "SHADOW_ONLY"
    duration_days: int = 7
    route_scope_json: List[str] = []
    automation_level: str = "LOW"
    auto_apply_enabled: bool = False
    operator_approval_required: bool = True
    safety_policy_json: Dict[str, Any] = {}

class UIPilotRolloutCreate(UIPilotRolloutBase):
    created_by: Optional[str] = None

class UIPilotRolloutSchema(UIPilotRolloutBase):
    id: str
    status: str
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class UIPilotEventCreate(BaseSchema):
    rollout_id: str
    event_type: str
    route: Optional[str] = None
    case_id: Optional[str] = None
    attempt_id: Optional[str] = None
    severity: str = "INFO"
    decision: Optional[str] = None
    payload_json: Dict[str, Any] = {}

class UIPilotEventSchema(UIPilotEventCreate):
    id: str
    created_at: datetime

class UIPilotMetricsSchema(BaseSchema):
    id: str
    rollout_id: str
    monitoring_runs: int = 0
    failures_detected: int = 0
    repair_cases_created: int = 0
    auto_diagnostics_started: int = 0
    prs_created: int = 0
    pr_agent_reviews: int = 0
    verifier_runs: int = 0
    governance_requests: int = 0
    approved_applies: int = 0
    rejected_repairs: int = 0
    rollbacks: int = 0
    false_positive_count: int = 0
    false_negative_count: int = 0
    avg_mttr_s: float = 0.0
    avg_governance_latency_s: float = 0.0
    operator_actions_count: int = 0
    updated_at: datetime

class UIOperatorActionLedgerCreate(BaseSchema):
    rollout_id: str
    operator: str
    action_type: str
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    rationale: str
    before_state_json: Dict[str, Any] = {}
    after_state_json: Dict[str, Any] = {}

class UIOperatorActionLedgerSchema(UIOperatorActionLedgerCreate):
    id: str
    created_at: datetime

class UIPilotFinalReportSchema(BaseSchema):
    id: str
    rollout_id: str
    status: str
    recommendation: str
    readiness_score: float = 0.0
    executive_summary: Optional[str] = None
    metrics_json: Dict[str, Any] = {}
    risks_json: List[str] = []
    incidents_json: List[str] = []
    operator_notes_json: List[str] = []
    report_path: Optional[str] = None
    evidence_hash: Optional[str] = None
    generated_at: datetime

# Phase 12: General Availability + Multi-Project Rollout Schemas

class UIProjectProfileBase(BaseSchema):
    project_key: str
    project_name: str
    environment: str = "PRODUCTION"
    owner: Optional[str] = None
    route_scope: List[str] = Field(alias="route_scope_json", default_factory=list)
    critical_routes: List[str] = Field(alias="critical_routes_json", default_factory=list)
    safety_policy: Dict[str, Any] = Field(alias="safety_policy_json", default_factory=dict)
    governance_policy: Dict[str, Any] = Field(alias="governance_policy_json", default_factory=dict)
    auto_repair_enabled: bool = False
    auto_apply_enabled: bool = False
    approval_required: bool = True
    status: str = "DRAFT"

class UIProjectProfileCreate(UIProjectProfileBase):
    pass

class UIProjectProfileSchema(UIProjectProfileBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

class UIRolloutWaveBase(BaseSchema):
    wave_name: str
    status: str = "PLANNED"
    project_keys: List[str] = Field(alias="project_keys_json", default_factory=list)
    rollout_mode: str = "GOVERNED_REPAIR"
    success_criteria: Dict[str, Any] = Field(alias="success_criteria_json", default_factory=dict)
    failure_criteria: Dict[str, Any] = Field(alias="failure_criteria_json", default_factory=dict)

class UIRolloutWaveCreate(UIRolloutWaveBase):
    pass

class UIRolloutWaveSchema(UIRolloutWaveBase):
    id: UUID
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    summary: Dict[str, Any] = Field(alias="summary_json", default_factory=dict)
    created_at: datetime
    updated_at: datetime

class UIProjectHealthSnapshotSchema(BaseSchema):
    id: UUID
    project_key: str
    health_score: float
    monitoring_status: Optional[str]
    open_cases: int
    critical_cases: int
    governance_waiting: int
    active_repairs: int
    last_incident_at: Optional[datetime]
    sla_status: Optional[str]
    slo_status: Optional[str]
    created_at: datetime

class UIGAReadinessAssessmentSchema(BaseSchema):
    id: UUID
    status: str
    readiness_score: float
    project_count: int
    passed_projects: int
    warning_projects: int
    blocked_projects: int
    blockers: List[str] = Field(alias="blockers_json")
    warnings: List[str] = Field(alias="warnings_json")
    recommendation: str
    assessed_by: Optional[str]
    created_at: datetime

class UIEnterpriseRunbookSchema(BaseSchema):
    id: UUID
    title: str
    version: str
    scope: Optional[str]
    content: str
    evidence_hash: Optional[str]
    generated_at: datetime
    created_at: datetime

class UIEnterpriseOverviewSchema(BaseSchema):
    total_projects: int
    active_projects: int
    blocked_projects: int
    global_health_score: float
    active_waves: int
    critical_route_coverage: float
    governance_waiting_total: int
    slo_compliance_rate: float
    ga_readiness_status: str
    runbook_status: str

# --- Phase 13: GA Hardening + Cross-Team Operations Schemas ---

class UIOperationsTeamBase(BaseSchema):
    team_key: str
    team_name: str
    responsibilities: List[str] = Field(alias="responsibilities_json", default_factory=list)
    owned_project_keys: List[str] = Field(alias="owned_project_keys_json", default_factory=list)
    escalation_channels: Dict[str, Any] = Field(alias="escalation_channels_json", default_factory=dict)
    oncall_policy: Dict[str, Any] = Field(alias="oncall_policy_json", default_factory=dict)
    status: str = "ACTIVE"

class UIOperationsTeamCreate(UIOperationsTeamBase):
    pass

class UIOperationsTeamSchema(UIOperationsTeamBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

class UIProjectOwnershipBase(BaseSchema):
    project_key: str
    owner_team_key: str
    technical_owner: str
    business_owner: str
    escalation_level: int = 1
    backup_owner: Optional[str] = None
    approval_policy: Dict[str, Any] = Field(alias="approval_policy_json", default_factory=dict)

class UIProjectOwnershipCreate(UIProjectOwnershipBase):
    pass

class UIProjectOwnershipSchema(UIProjectOwnershipBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

class UIMaintenancePolicyBase(BaseSchema):
    project_key: str
    policy_name: str
    maintenance_window: Dict[str, Any] = Field(alias="maintenance_window_json", default_factory=dict)
    allowed_actions: List[str] = Field(alias="allowed_actions_json", default_factory=list)
    blocked_actions: List[str] = Field(alias="blocked_actions_json", default_factory=list)
    auto_repair_allowed: bool = True
    auto_apply_allowed: bool = False
    approval_required: bool = True
    rollback_required: bool = True

class UIMaintenancePolicyCreate(UIMaintenancePolicyBase):
    pass

class UIMaintenancePolicySchema(UIMaintenancePolicyBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

class UIReleaseRecordBase(BaseSchema):
    version: str
    release_type: str
    project_keys: List[str] = Field(alias="project_keys_json", default_factory=list)
    summary: str
    changes: List[Dict[str, Any]] = Field(alias="changes_json", default_factory=list)
    risk_summary: Dict[str, Any] = Field(alias="risk_summary_json", default_factory=dict)
    compatibility_notes: Optional[str] = None
    rollback_notes: Optional[str] = None
    evidence_hash: Optional[str] = None

class UIReleaseRecordCreate(UIReleaseRecordBase):
    pass

class UIReleaseRecordSchema(UIReleaseRecordBase):
    id: UUID
    created_at: datetime

class UICompatibilityCheckBase(BaseSchema):
    project_key: Optional[str] = None
    version: Optional[str] = None
    status: str
    breaking_changes: List[str] = Field(alias="breaking_changes_json", default_factory=list)
    deprecated_features: List[str] = Field(alias="deprecated_features_json", default_factory=list)
    migration_required: bool = False
    migration_notes: Optional[str] = None
    evidence_hash: Optional[str] = None

class UICompatibilityCheckCreate(UICompatibilityCheckBase):
    pass

class UICompatibilityCheckSchema(UICompatibilityCheckBase):
    id: UUID
    checked_at: datetime

class UISLOBreachBase(BaseSchema):
    project_key: str
    slo_name: str
    severity: str
    observed_value: float
    target_value: float
    breach_started_at: datetime
    breach_resolved_at: Optional[datetime] = None
    status: str = "OPEN"
    linked_incident_id: Optional[UUID] = None
    remediation_plan: Dict[str, Any] = Field(alias="remediation_plan_json", default_factory=dict)

class UISLOBreachCreate(UISLOBreachBase):
    pass

class UISLOBreachSchema(UISLOBreachBase):
    id: UUID
    created_at: datetime

class UIEvidenceRetentionPolicyBase(BaseSchema):
    policy_name: str
    retention_days: int
    evidence_type: str
    archive_after_days: int
    delete_after_days: int
    legal_hold: bool = False

class UIEvidenceRetentionPolicyCreate(UIEvidenceRetentionPolicyBase):
    pass

class UIEvidenceRetentionPolicySchema(UIEvidenceRetentionPolicyBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

# --- Phase 14: Enterprise FinOps + Capacity Planning + Cost-Aware Autonomy Schemas ---

class UICostEventBase(BaseSchema):
    project_key: str
    team_key: Optional[str] = None
    source_type: str
    source_id: Optional[str] = None
    operation_type: str
    provider: Optional[str] = None
    model: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    tool_calls: int = 0
    duration_ms: int = 0
    estimated_cost_usd: float = 0.0
    metadata: Dict[str, Any] = Field(alias="metadata_json", default_factory=dict)

class UICostEventCreate(UICostEventBase):
    pass

class UICostEventSchema(UICostEventBase):
    id: UUID
    created_at: datetime

class UIBudgetPolicyBase(BaseSchema):
    project_key: Optional[str] = None
    team_key: Optional[str] = None
    daily_budget_usd: float = 10.0
    weekly_budget_usd: float = 50.0
    monthly_budget_usd: float = 200.0
    hard_limit_usd: float = 500.0
    soft_limit_percent: float = 80.0
    action_on_soft_limit: str = "NOTIFY"
    action_on_hard_limit: str = "BLOCK"

class UIBudgetPolicyCreate(UIBudgetPolicyBase):
    pass

class UIBudgetPolicySchema(UIBudgetPolicyBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

class UICostAnomalyBase(BaseSchema):
    project_key: str
    anomaly_type: str
    severity: str = "MEDIUM"
    observed_cost_usd: float
    expected_cost_usd: float
    deviation_percent: float
    reason: Optional[str] = None
    linked_event_ids: List[str] = Field(alias="linked_event_ids_json", default_factory=list)
    status: str = "OPEN"

class UICostAnomalyCreate(UICostAnomalyBase):
    pass

class UICostAnomalySchema(UICostAnomalyBase):
    id: UUID
    created_at: datetime
    resolved_at: Optional[datetime] = None

class UICapacityForecastBase(BaseSchema):
    project_key: str
    forecast_window: str
    expected_monitoring_runs: int = 0
    expected_repair_attempts: int = 0
    expected_verifier_runs: int = 0
    expected_llm_calls: int = 0
    expected_cost_usd: float = 0.0
    confidence: float = 0.0

class UICapacityForecastCreate(UICapacityForecastBase):
    pass

class UICapacityForecastSchema(UICapacityForecastBase):
    id: UUID
    created_at: datetime

class UIFinOpsRecommendationBase(BaseSchema):
    project_key: str
    recommendation_type: str
    priority: str = "MEDIUM"
    title: str
    description: Optional[str] = None
    expected_savings_usd: float = 0.0
    risk_impact: str = "LOW"
    status: str = "PENDING"

class UIFinOpsRecommendationCreate(UIFinOpsRecommendationBase):
    pass

class UIFinOpsRecommendationSchema(UIFinOpsRecommendationBase):
    id: UUID
    created_at: datetime
    applied_at: Optional[datetime] = None

class UIFinOpsOverviewSchema(BaseSchema):
    total_cost_today: float
    total_cost_week: float
    total_cost_month: float
    project_cost_distribution: List[Dict[str, Any]]
    team_cost_distribution: List[Dict[str, Any]]
    operation_type_distribution: List[Dict[str, Any]]
    budget_usage_percent: float
    active_anomalies_count: int
    forecasted_next_30d_cost: float
    potential_savings_usd: float

# --- Phase 15: Autonomous Ecosystem Governance + Policy-as-Code (PaC) Schemas ---

class PolicyScope(str, Enum):
    GLOBAL = "GLOBAL"
    PROJECT = "PROJECT"
    TEAM = "TEAM"
    ROUTE = "ROUTE"
    ACTION = "ACTION"

class PolicyDecision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    REQUIRE_MANUAL_REVIEW = "REQUIRE_MANUAL_REVIEW"
    REQUIRE_MAINTENANCE_WINDOW = "REQUIRE_MAINTENANCE_WINDOW"
    BLOCKED_BY_BUDGET = "BLOCKED_BY_BUDGET"
    BLOCKED_BY_COMPLIANCE = "BLOCKED_BY_COMPLIANCE"
    SIMULATION_ONLY = "SIMULATION_ONLY"

class PolicyRuleType(str, Enum):
    AUTO_REPAIR = "AUTO_REPAIR"
    AUTO_APPLY = "AUTO_APPLY"
    GOVERNANCE_APPROVAL = "GOVERNANCE_APPROVAL"
    BUDGET = "BUDGET"
    MAINTENANCE_WINDOW = "MAINTENANCE_WINDOW"
    ROUTE_CRITICALITY = "ROUTE_CRITICALITY"
    COMPLIANCE = "COMPLIANCE"
    CHAOS_DRILL = "CHAOS_DRILL"
    NOTIFICATION = "NOTIFICATION"
    CRISIS_MODE = "CRISIS_MODE"
    RELEASE = "RELEASE"

class PolicyProposalStatus(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    APPLIED = "APPLIED"
    SUPERSEDED = "SUPERSEDED"

class UIPolicyRuleBase(BaseSchema):
    policy_key: str
    scope: PolicyScope = PolicyScope.GLOBAL
    project_key: Optional[str] = None
    rule_type: PolicyRuleType = PolicyRuleType.AUTO_REPAIR
    priority: int = 100
    enabled: bool = True
    rule_definition: Dict[str, Any] = Field(alias="rule_definition_json", default_factory=dict)
    description: Optional[str] = None

class UIPolicyRuleCreate(UIPolicyRuleBase):
    created_by: str

class UIPolicyRuleSchema(UIPolicyRuleBase):
    id: UUID
    created_by: str
    created_at: datetime
    updated_at: datetime

class UIPolicyEvaluationSchema(BaseSchema):
    id: UUID
    policy_key: Optional[str] = None
    project_key: str
    action_type: str
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    decision: PolicyDecision
    reason: Optional[str] = None
    matched_rules: Dict[str, Any] = Field(alias="matched_rules_json")
    input_context: Dict[str, Any] = Field(alias="input_context_json")
    output: Dict[str, Any] = Field(alias="output_json")
    evaluated_at: datetime

class UIPolicyConflictSchema(BaseSchema):
    id: UUID
    global_policy_key: str
    project_policy_key: str
    project_key: str
    conflict_type: str
    resolution: str
    reason: str
    created_at: datetime
    resolved_at: Optional[datetime] = None

class UIPolicyProposalBase(BaseSchema):
    proposal_type: str # NEW, UPDATE, DELETE
    policy_key: str
    scope: PolicyScope
    project_key: Optional[str] = None
    proposed_rule: Dict[str, Any] = Field(alias="proposed_rule_json")
    rationale: str
    risk_level: str

class UIPolicyProposalCreate(UIPolicyProposalBase):
    proposed_by: str

class UIPolicyProposalSchema(UIPolicyProposalBase):
    id: UUID
    status: PolicyProposalStatus
    proposed_by: str
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime

class UIAutonomousOverrideCreate(BaseSchema):
    action_type: str
    target_type: str
    target_id: str
    blocked_policy_key: str
    override_reason: str
    operator: str
    risk_level: str
    approval_id: Optional[str] = None

class UIAutonomousOverrideSchema(UIAutonomousOverrideCreate):
    id: UUID
    evidence_hash: Optional[str] = None
    created_at: datetime

class UIComplianceFindingSchema(BaseSchema):
    id: UUID
    project_key: str
    source_type: str
    source_id: str
    standard: str
    severity: str
    finding_type: str
    description: str
    recommendation: Optional[str] = None
    status: str
    created_at: datetime
    resolved_at: Optional[datetime] = None

# --- Phase 16: Multi-Tenant Federation + Cross-Cluster Governance Schemas ---

class UITenantProfileCreate(BaseModel):
    tenant_key: str
    tenant_name: str
    status: Optional[str] = "ACTIVE"
    governance_level: Optional[str] = "STANDARD"
    contact_info: Optional[Dict[str, Any]] = {}
    tenant_metadata: Optional[Dict[str, Any]] = {}

class UITenantProfileSchema(BaseSchema):
    id: UUID
    tenant_key: str
    tenant_name: str
    status: str
    governance_level: str
    contact_info: Dict[str, Any]
    tenant_metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

class UIClusterProfileCreate(BaseModel):
    cluster_key: str
    cluster_name: str
    region: Optional[str] = "global"
    environment: Optional[str] = "production"
    provider: Optional[str] = "Sovereign"
    cluster_metadata: Optional[Dict[str, Any]] = {}

class UIClusterProfileSchema(BaseSchema):
    id: UUID
    cluster_key: str
    cluster_name: str
    region: str
    environment: str
    provider: str
    status: str
    cluster_metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

class UITenantProjectBindingCreate(BaseModel):
    tenant_key: str
    cluster_key: Optional[str] = None
    project_key: str

class UITenantProjectBindingSchema(BaseSchema):
    id: UUID
    tenant_key: str
    cluster_key: Optional[str]
    project_key: str
    binding_status: str
    created_at: datetime

class UIClusterHealthSnapshotCreate(BaseModel):
    cluster_key: str
    health_score: float
    active_repairs: int = 0
    failed_repairs_24h: int = 0
    latency_ms: int = 0
    status_brief: str
    metrics_json: Optional[Dict[str, Any]] = {}

class UIClusterHealthSnapshotSchema(BaseSchema):
    id: UUID
    cluster_key: str
    health_score: float
    active_repairs: int
    failed_repairs_24h: int
    latency_ms: int
    status_brief: str
    metrics_json: Dict[str, Any]
    captured_at: datetime

# --- Phase 17: Resiliency Mesh Schemas ---

class MeshNodeStatus(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    SATURATED = "SATURATED"
    UNREACHABLE = "UNREACHABLE"
    FAILOVER_ACTIVE = "FAILOVER_ACTIVE"
    MAINTENANCE = "MAINTENANCE"
    BLOCKED_BY_POLICY = "BLOCKED_BY_POLICY"

class FailoverTrigger(str, Enum):
    HEALTH_DEGRADATION = "HEALTH_DEGRADATION"
    LATENCY_SPIKE = "LATENCY_SPIKE"
    COST_LIMIT = "COST_LIMIT"
    CAPACITY_EXHAUSTED = "CAPACITY_EXHAUSTED"
    SLO_BREACH = "SLO_BREACH"
    REGION_OUTAGE = "REGION_OUTAGE"
    CHAOS_DRILL = "CHAOS_DRILL"
    MANUAL_OPERATOR = "MANUAL_OPERATOR"

class WorkloadType(str, Enum):
    MONITORING_RUN = "MONITORING_RUN"
    STAGEHAND_DIAGNOSTIC = "STAGEHAND_DIAGNOSTIC"
    OPENSWE_REPAIR = "OPENSWE_REPAIR"
    PR_AGENT_REVIEW = "PR_AGENT_REVIEW"
    VERIFIER_MESH_RUN = "VERIFIER_MESH_RUN"
    CHAOS_DRILL = "CHAOS_DRILL"
    PROOF_PACK_GENERATION = "PROOF_PACK_GENERATION"
    POSTMORTEM_GENERATION = "POSTMORTEM_GENERATION"

class UIResiliencyMeshNodeCreate(BaseModel):
    tenant_key: str
    cluster_key: str
    region: str
    environment: str
    status: MeshNodeStatus = MeshNodeStatus.HEALTHY

class UIResiliencyMeshNodeSchema(BaseSchema):
    id: UUID
    tenant_key: str
    cluster_key: str
    region: str
    environment: str
    status: MeshNodeStatus
    health_score: float
    capacity_score: float
    cost_score: float
    latency_ms: int
    active_repairs: int
    queue_depth: int
    last_heartbeat_at: datetime
    created_at: datetime
    updated_at: datetime

class UIClusterFailoverEventCreate(BaseModel):
    source_cluster_key: str
    target_cluster_key: str
    tenant_key: str
    reason: str
    trigger_type: FailoverTrigger
    severity: str = "medium"
    decision_json: Optional[Dict[str, Any]] = {}

class UIClusterFailoverEventSchema(BaseSchema):
    id: UUID
    source_cluster_key: str
    target_cluster_key: str
    tenant_key: str
    reason: str
    trigger_type: FailoverTrigger
    severity: str
    decision_json: Dict[str, Any]
    success: bool
    started_at: datetime
    completed_at: Optional[datetime]
    evidence_hash: Optional[str]
    created_at: datetime

class UIGlobalLoadSteeringDecisionSchema(BaseSchema):
    id: UUID
    tenant_key: str
    project_key: str
    source_cluster_key: Optional[str]
    selected_cluster_key: str
    workload_type: WorkloadType
    decision_reason: str
    health_score: float
    cost_score: float
    latency_score: float
    policy_score: float
    final_score: float
    created_at: datetime

class UIMeshChaosRunCreate(BaseModel):
    scenario_name: str
    target_cluster_key: str
    target_region: str
    chaos_type: str
    expected_behavior: str

class UIMeshChaosRunSchema(BaseSchema):
    id: UUID
    scenario_name: str
    target_cluster_key: str
    target_region: str
    chaos_type: str
    expected_behavior: str
    detected_behavior: str
    recovery_success: bool
    failover_triggered: bool
    started_at: datetime
    completed_at: Optional[datetime]
    evidence_path: Optional[str]
    created_at: datetime

class UIGlobalSLOSnapshotSchema(BaseSchema):
    id: UUID
    tenant_key: Optional[str]
    federation_health_score: float
    global_mttr_s: float
    global_detection_latency_s: float
    repair_success_rate: float
    failover_success_rate: float
    policy_violation_count: int
    evidence_sync_success_rate: float
    created_at: datetime

class UIAutomatedPostmortemSchema(BaseSchema):
    id: UUID
    incident_id: Optional[UUID]
    tenant_key: str
    cluster_key: str
    title: str
    root_cause: str
    timeline_json: Dict[str, Any]
    impact_summary: str
    contributing_factors_json: List[Dict[str, Any]]
    remediation_actions_json: List[Dict[str, Any]]
    prevention_actions_json: List[Dict[str, Any]]
    evidence_hash: Optional[str]
    generated_at: datetime

class UIExternalToolBase(BaseModel):
    tool_key: str
    tool_name: str
    tool_type: str
    provider: str
    description: Optional[str] = None
    enabled: bool = True
    risk_level: str = "MEDIUM"
    tenant_scope_json: List[str] = []
    project_scope_json: List[str] = []
    allowed_actions_json: List[str] = []
    blocked_actions_json: List[str] = []
    requires_approval: bool = False
    requires_sandbox: bool = False
    cost_policy_json: Dict[str, Any] = {}

class UIExternalToolCreate(UIExternalToolBase):
    pass

class UIExternalToolSchema(UIExternalToolBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)

class UIMCPServerBase(BaseModel):
    server_key: str
    server_name: str
    endpoint: str
    transport_type: str = "stdio"
    enabled: bool = True
    tenant_scope_json: List[str] = []
    allowed_tools_json: List[str] = []
    blocked_tools_json: List[str] = []
    auth_mode: str = "NONE"
    risk_level: str = "MEDIUM"

class UIMCPServerCreate(UIMCPServerBase):
    pass

class UIMCPServerSchema(UIMCPServerBase):
    id: uuid.UUID
    health_status: str
    last_checked_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)

class UIToolPermissionBase(BaseModel):
    tool_key: str
    tenant_key: str
    project_key: str
    action_type: str
    decision: str
    reason: str
    requires_approval: bool = False
    requires_sandbox: bool = False

class UIToolPermissionCreate(UIToolPermissionBase):
    pass

class UIToolPermissionSchema(UIToolPermissionBase):
    id: uuid.UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class UIToolCallAuditSchema(BaseModel):
    id: uuid.UUID
    tool_key: str
    server_key: Optional[str]
    tenant_key: str
    project_key: str
    caller_type: str
    caller_id: str
    action_type: str
    input_hash: str
    output_hash: str
    redaction_applied: bool
    policy_decision: str
    risk_level: str
    cost_estimate_usd: float
    latency_ms: int
    status: str
    error_message: Optional[str]
    evidence_hash: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class UIToolPolicyViolationSchema(BaseModel):
    id: uuid.UUID
    tool_key: str
    server_key: Optional[str]
    tenant_key: str
    project_key: str
    violation_type: str
    severity: str
    description: str
    blocked: bool
    incident_id: Optional[uuid.UUID]
    evidence_hash: str
    created_at: datetime
    resolved_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)

class UIProviderHealthSchema(BaseModel):
    id: uuid.UUID
    provider: str
    status: str
    latency_ms: int
    error_rate: float
    cost_spike_detected: bool
    last_success_at: Optional[datetime]
    last_failure_at: Optional[datetime]
    health_score: float
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class UIThirdPartyRiskAssessmentSchema(BaseModel):
    id: uuid.UUID
    provider: str
    tool_key: Optional[str]
    risk_score: float
    risk_level: str
    findings_json: List[Dict[str, Any]]
    recommendation: str
    assessed_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ToolCallEvaluationRequest(BaseModel):
    tool_key: str
    server_key: Optional[str] = None
    tenant_key: str
    project_key: str
    action_type: str
    input_data: Dict[str, Any]

class ToolCallEvaluationResponse(BaseModel):
    decision: str # ALLOW, DENY, REQUIRE_APPROVAL, REQUIRE_SANDBOX
    reason: str
    risk_level: str
    redaction_required: bool
    matched_policies: List[str]
    required_controls: List[str]

# --- Phase 19: Sovereign Identity Framework v2 Schemas ---

class UISovereignIdentityBase(BaseModel):
    identity_key: str
    identity_type: str
    display_name: str
    tenant_key: str
    project_key: str
    cluster_key: str
    allowed_actions_json: List[str] = []
    trust_level: str = "STANDARD"
    status: str = "ACTIVE"
    public_key_fingerprint: str

class UISovereignIdentitySchema(UISovereignIdentityBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UICapabilityTokenBase(BaseModel):
    subject_identity_key: str
    scope_json: Dict[str, Any] = {}
    allowed_actions_json: List[str] = []
    expires_at: datetime
    issued_by: str

class UICapabilityTokenSchema(UICapabilityTokenBase):
    id: uuid.UUID
    token_id: str
    revoked_at: Optional[datetime] = None
    evidence_hash: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UIAgentHandshakeBase(BaseModel):
    source_identity_key: str
    target_identity_key: str
    nonce: str
    signed_context_hash: str
    tenant_key: str
    project_key: str
    cluster_key: str
    action_type: str
    risk_level: str

class UIAgentHandshakeSchema(UIAgentHandshakeBase):
    id: uuid.UUID
    handshake_status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UIIdentityAuditEventSchema(BaseModel):
    id: uuid.UUID
    identity_key: str
    event_type: str
    action_type: Optional[str] = None
    decision: str
    reason: str
    tenant_key: str
    project_key: str
    cluster_key: str
    evidence_hash: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UITrustScoreSchema(BaseModel):
    id: uuid.UUID
    identity_key: str
    trust_score: float
    success_count: int
    policy_violation_count: int
    failed_handshake_count: int
    stale_token_count: int
    last_updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class HandshakeRequest(BaseModel):
    source_identity_key: str
    target_identity_key: str
    action_type: str
    tenant_key: str
    project_key: str
    cluster_key: str
    nonce: str
    signature: str # Context hash signed by source

class TokenIssueRequest(BaseModel):
    identity_key: str
    scope: Dict[str, Any]
    actions: List[str]
    duration_minutes: int = 60

# Phase 20: Cognitive Integrity Schemas

class UICognitiveIntegrityCheckBase(BaseModel):
    source_type: str
    source_id: str
    agent_name: str
    output_type: str
    
class UICognitiveIntegrityCheckSchema(UICognitiveIntegrityCheckBase):
    id: UUID
    status: str
    integrity_score: float
    hallucination_score: float
    evidence_grounding_score: float
    semantic_drift_score: float
    claim_verification_score: float
    decision: Optional[str] = None
    reason: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UILLMClaimBase(BaseModel):
    check_id: UUID
    claim_text: str
    claim_type: str

class UILLMClaimSchema(UILLMClaimBase):
    id: UUID
    verification_status: str
    evidence_refs_json: Optional[Dict[str, Any]] = None
    confidence: float
    failure_reason: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UIHallucinationFindingBase(BaseModel):
    check_id: UUID
    finding_type: str
    severity: str
    description: str

class UIHallucinationFindingSchema(UIHallucinationFindingBase):
    id: UUID
    unsupported_reference: Optional[str] = None
    suggested_action: Optional[str] = None
    blocked: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UISemanticDriftEventBase(BaseModel):
    source_type: str
    source_id: str
    drift_type: str
    drift_score: float
    severity: str
    description: str

class UISemanticDriftEventSchema(UISemanticDriftEventBase):
    id: UUID
    expected_context_hash: str
    actual_context_hash: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UICognitivePolicyDecisionBase(BaseModel):
    check_id: UUID
    action_type: str
    decision: str
    reason: str

class UICognitivePolicyDecisionSchema(UICognitivePolicyDecisionBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UICognitiveIntegrityVerifyRequest(BaseModel):
    source_type: str
    source_id: str
    agent_name: str
    output_text: str
    context_json: Optional[Dict[str, Any]] = None

class CognitiveCheckRequest(BaseModel):
    source_type: str
    source_id: str
    agent_name: str
    output_type: str
    content: str # The LLM output to verify
    context_data: Optional[Dict[str, Any]] = None # Optional expected context

# --- Phase 21: Security Posture & Compliance ---

class UISecurityPostureScoreSchema(BaseSchema):
    id: UUID
    overall_score: float
    identity_score: float
    policy_score: float
    isolation_score: float
    governance_score: float
    evidence_score: float
    posture_level: str
    tenant_key: Optional[str]
    created_at: datetime

class UIComplianceControlSchema(BaseSchema):
    id: UUID
    control_key: str
    domain: str
    title: str
    description: str
    severity: str
    is_mandatory: bool
    created_at: datetime

class UISecurityPostureFindingSchema(BaseSchema):
    id: UUID
    control_key: str
    status: str
    evidence_hash: Optional[str]
    rationale: str
    tenant_key: Optional[str]
    cluster_key: Optional[str]
    last_check_at: datetime
    created_at: datetime

class UISecurityCertificationSchema(BaseSchema):
    id: UUID
    cert_id: str
    overall_score: float
    compliance_score: float
    posture_level: str
    summary: Dict[str, Any] = Field(alias="summary_json")
    findings: List[Dict[str, Any]] = Field(alias="findings_json")
    certified_by: str
    evidence_ledger_hash: Optional[str]
    tenant_key: Optional[str]
    created_at: datetime

# --- Phase 22: Security Remediation & Auto-Fix ---

class UISecurityRemediationPlanSchema(BaseSchema):
    id: UUID
    finding_id: UUID
    finding_type: str
    severity: str
    risk_level: str
    remediation_type: str
    recommended_action: str
    affected_module: Optional[str]
    affected_policy: Optional[str]
    affected_route: Optional[str]
    requires_approval: bool
    requires_patch: bool
    requires_operator: bool
    status: str
    created_at: datetime
    updated_at: datetime

class UISecurityAutoFixAttemptSchema(BaseSchema):
    id: UUID
    remediation_plan_id: UUID
    finding_id: UUID
    status: str
    fix_strategy: str
    patch_path: Optional[str]
    pr_url: Optional[str]
    verifier_status: Optional[str]
    governance_status: Optional[str]
    posture_before_score: float
    posture_after_score: Optional[float]
    error_message: Optional[str]
    started_at: datetime
    finished_at: Optional[datetime]
    created_at: datetime

class UIComplianceFixResultSchema(BaseSchema):
    id: UUID
    finding_id: UUID
    remediation_plan_id: UUID
    certification_before_id: Optional[UUID]
    certification_after_id: Optional[UUID]
    compliance_status_before: str
    compliance_status_after: str
    fixed: bool
    residual_risk: Optional[str]
    evidence_hash: Optional[str]
    created_at: datetime

class UISecurityRemediationEventSchema(BaseSchema):
    id: UUID
    finding_id: UUID
    plan_id: UUID
    attempt_id: Optional[UUID]
    event_type: str
    message: str
    payload: Dict[str, Any] = Field(alias="payload_json")
    evidence_hash: Optional[str]
    created_at: datetime

class UIAttackSurfaceAssetSchema(BaseSchema):
    id: UUID
    asset_key: str
    asset_type: str
    project_key: Optional[str]
    tenant_key: Optional[str]
    cluster_key: Optional[str]
    exposure_level: str
    criticality: str
    owner_team: Optional[str]
    metadata: Dict[str, Any] = Field(validation_alias="metadata_json")
    created_at: datetime
    updated_at: datetime

class UIThreatModelSchema(BaseSchema):
    id: UUID
    model_name: str
    scope: str
    tenant_key: Optional[str]
    project_key: Optional[str]
    cluster_key: Optional[str]
    status: str
    generated_by: str
    summary: Dict[str, Any] = Field(validation_alias="summary_json")
    evidence_hash: Optional[str]
    created_at: datetime
    updated_at: datetime

class UIAttackPathSchema(BaseSchema):
    id: UUID
    threat_model_id: UUID
    path_name: str
    path_type: str
    source_asset_key: str
    target_asset_key: str
    attack_steps: List[Dict[str, Any]] = Field(validation_alias="attack_steps_json")
    required_conditions: List[str] = Field(validation_alias="required_conditions_json")
    risk_score: float
    severity: str
    feasibility: float
    impact: float
    mitigation_status: str
    created_at: datetime

class UIAttackSimulationRunSchema(BaseSchema):
    id: UUID
    attack_path_id: UUID
    status: str
    simulation_mode: str
    started_at: datetime
    finished_at: Optional[datetime]
    detected_controls: List[str] = Field(validation_alias="detected_controls_json")
    bypassed_controls: List[str] = Field(validation_alias="bypassed_controls_json")
    blocked_by: Optional[Dict[str, Any]] = Field(validation_alias="blocked_by_json")
    result_summary: Dict[str, Any] = Field(validation_alias="result_summary_json")
    evidence_hash: Optional[str]
    created_at: datetime

class UIThreatMitigationSchema(BaseSchema):
    id: UUID
    attack_path_id: UUID
    mitigation_type: str
    recommendation: str
    related_policy_key: Optional[str]
    related_control_id: Optional[str]
    remediation_plan_id: Optional[UUID]
    status: str
    created_at: datetime
    updated_at: datetime

class UIThreatSummarySchema(BaseSchema):
    total_assets: int
    critical_assets: int
    attack_path_count: int
    high_risk_paths: int
    simulation_success_rate: float
    mitigation_coverage: float

# --- Phase 24: Autonomous Red Teaming + Adversarial Drift Detection ---

class UIRedTeamScenarioSchema(BaseSchema):
    id: UUID
    scenario_key: str
    scenario_name: str
    description: str
    source_attack_path_id: Optional[UUID]
    scenario_type: str
    target_domain: str
    target_asset_key: Optional[str]
    tenant_key: Optional[str]
    project_key: Optional[str]
    cluster_key: Optional[str]
    risk_level: str
    safety_mode: str
    expected_control: Optional[str]
    expected_block_reason: Optional[str]
    payload_template: Dict[str, Any] = Field(validation_alias="payload_template_json")
    enabled: bool
    created_at: datetime
    updated_at: datetime

class UIRedTeamRunSchema(BaseSchema):
    id: UUID
    scenario_id: UUID
    status: str
    started_at: datetime
    finished_at: Optional[datetime]
    safety_mode: str
    detected_by_control: Optional[str]
    blocked_by_control: Optional[str]
    bypassed_controls: List[str] = Field(validation_alias="bypassed_controls_json")
    triggered_controls: List[str] = Field(validation_alias="triggered_controls_json")
    result_summary: Dict[str, Any] = Field(validation_alias="result_summary_json")
    evidence_hash: Optional[str]
    created_at: datetime

class UIAdversarialProbeSchema(BaseSchema):
    id: UUID
    run_id: UUID
    probe_type: str
    target_domain: str
    input_payload_hash: Optional[str]
    expected_decision: str
    actual_decision: str
    passed: bool
    failure_reason: Optional[str]
    created_at: datetime

class UIAdversarialDriftEventSchema(BaseSchema):
    id: UUID
    run_id: Optional[UUID]
    domain: str
    drift_type: str
    baseline_hash: Optional[str]
    observed_behavior_hash: Optional[str]
    drift_score: float
    severity: str
    description: str
    created_at: datetime

class UIRedTeamFindingSchema(BaseSchema):
    id: UUID
    run_id: UUID
    scenario_id: UUID
    finding_type: str
    severity: str
    description: str
    affected_control: Optional[str]
    affected_domain: str
    feasible: bool
    remediation_plan_id: Optional[UUID]
    incident_id: Optional[UUID]
    evidence_hash: Optional[str]
    created_at: datetime
    resolved_at: Optional[datetime]

class UIRedTeamReportSchema(BaseSchema):
    id: UUID
    report_name: str
    period_start: datetime
    period_end: datetime
    total_scenarios: int
    passed_scenarios: int
    failed_scenarios: int
    critical_findings: int
    high_findings: int
    drift_events: int
    executive_summary: str
    report_path: Optional[str]
    evidence_hash: Optional[str]
    generated_at: datetime

class UIRedTeamOverviewSchema(BaseSchema):
    total_scenarios: int
    active_operations: int
    success_rate: float
    avg_detection_latency: float
    critical_drifts: int
    last_run_at: Optional[datetime]


class UIIncidentWarRoomSchema(BaseSchema):
    id: UUID
    incident_key: str
    title: str
    severity: str
    status: str
    source_type: str
    source_id: Optional[UUID]
    tenant_key: Optional[str]
    project_key: Optional[str]
    cluster_key: Optional[str]
    assigned_commander: Optional[str]
    owner_team: Optional[str]
    blast_radius: Dict[str, Any] = Field(alias="blast_radius_json")
    business_impact_score: float
    executive_risk_score: float
    opened_at: datetime
    resolved_at: Optional[datetime]
    evidence_hash: Optional[str]
    created_at: datetime

class UIIncidentTimelineEventSchema(BaseSchema):
    id: UUID
    war_room_id: UUID
    event_type: str
    actor: str
    message: str
    source_ref: Optional[str]
    payload: Dict[str, Any] = Field(alias="payload_json")
    created_at: datetime
    evidence_hash: Optional[str]

class UIExecutiveRiskSnapshotSchema(BaseSchema):
    id: UUID
    snapshot_time: datetime
    global_risk_score: float
    active_p0_count: int
    active_p1_count: int
    affected_tenants: int
    affected_clusters: int
    open_remediations: int
    governance_waiting: int
    executive_summary: str
    created_at: datetime

class UIIncidentActionItemSchema(BaseSchema):
    id: UUID
    war_room_id: UUID
    action_type: str
    title: str
    owner: str
    status: str
    due_at: Optional[datetime]
    linked_remediation_id: Optional[UUID]
    linked_postmortem_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime

class UIExecutiveRiskReportSchema(BaseSchema):
    id: UUID
    report_name: str
    period_start: datetime
    period_end: datetime
    total_incidents: int
    p0_count: int
    p1_count: int
    mttr_s: float
    unresolved_risks: List[Dict[str, Any]] = Field(alias="unresolved_risks_json")
    top_risk_domains: List[str] = Field(alias="top_risk_domains_json")
    recommendation: str
    report_path: Optional[str]
    evidence_hash: Optional[str]
    generated_at: datetime

# Request/Response schemas
class WarRoomCreateRequest(BaseModel):
    source_type: str
    source_id: UUID
    title: Optional[str] = None
    severity: Optional[str] = None

class WarRoomAssignCommanderRequest(BaseModel):
    commander: str

class UIIncidentActionItemCreate(BaseModel):
    action_type: str
    title: str
    owner: str
    due_at: Optional[datetime] = None

class WarRoomResolveRequest(BaseModel):
    rationale: str
    actor: str

class ExecutiveRiskOverview(BaseSchema):
    global_risk_score: float
    active_p0_count: int
    active_p1_count: int
    active_p2_count: int
    active_p3_count: int
    affected_tenants: int
    affected_clusters: int
    open_remediations: int
    governance_waiting: int
    mttr_s: float
    top_affected_tenants: List[str]
    top_affected_clusters: List[str]
    unresolved_critical_risks: List[Dict[str, Any]]
    last_report_id: Optional[UUID] = None


# --- Phase 27: Autonomous Remediation Execution (Auto-Patch v2) ---

class AutoPatchExecutionSchema(BaseSchema):
    id: UUID
    execution_key: str
    source_type: str
    source_id: Optional[UUID]
    war_room_id: Optional[UUID]
    action_item_id: Optional[UUID]
    remediation_plan_id: Optional[UUID]
    status: str
    risk_level: str
    patch_strategy: Optional[str]
    patch_path: Optional[str]
    pr_url: Optional[str]
    branch_name: Optional[str]
    governance_approval_id: Optional[UUID]
    rollback_snapshot_path: Optional[str]
    error_message: Optional[str]
    evidence_hash: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    created_at: datetime

class PatchCandidateSchema(BaseSchema):
    id: UUID
    execution_id: UUID
    candidate_key: str
    strategy: str
    affected_files: List[str] = Field(alias="affected_files_json")
    affected_routes: List[str] = Field(alias="affected_routes_json")
    summary: str
    risk_level: str
    cognitive_integrity_score: float
    pr_agent_score: float
    verifier_score: float
    selected: bool
    rejected_reason: Optional[str]
    created_at: datetime

class VerificationRunV2Schema(BaseSchema):
    id: UUID
    execution_id: UUID
    status: str
    lint_status: str
    typecheck_status: str
    unit_test_status: str
    build_status: str
    playwright_status: str
    affected_route_status: str
    security_posture_status: str
    cognitive_integrity_status: str
    result_summary: Dict[str, Any] = Field(alias="result_summary_json")
    logs_path: Optional[str]
    created_at: datetime

class PostApplyValidationSchema(BaseSchema):
    id: UUID
    execution_id: UUID
    status: str
    route_health_after: Dict[str, Any] = Field(alias="route_health_after_json")
    posture_score_before: float
    posture_score_after: float
    evidence_chain_valid: bool
    regression_passed: bool
    rollback_required: bool
    residual_risk: Optional[str]
    created_at: datetime

class RollbackExecutionSchema(BaseSchema):
    id: UUID
    execution_id: UUID
    status: str
    rollback_reason: str
    rollback_snapshot_path: str
    rollback_result: Dict[str, Any] = Field(alias="rollback_result_json")
    evidence_hash: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    created_at: datetime

class AutoPatchStartRequest(BaseModel):
    source_type: str
    source_id: UUID
    war_room_id: Optional[UUID] = None
    action_item_id: Optional[UUID] = None
    remediation_plan_id: Optional[UUID] = None
    risk_level: Optional[str] = "MEDIUM"

class AutoPatchActionRequest(BaseModel):
    rationale: str
    actor: str

# --- Phase 28: Auto-Remediation Observability + Multi-Agent Patch Negotiation ---

class AutoPatchTraceSchema(BaseSchema):
    execution_id: UUID
    step_name: str
    status: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    agent_name: Optional[str] = None
    cost_usd: float = 0.0
    token_input: int = 0
    token_output: int = 0
    error_message: Optional[str] = None
    evidence_hash: Optional[str] = None
    metadata_json: Dict[str, Any] = {}
    created_at: datetime

class PatchAgentOpinionSchema(BaseSchema):
    execution_id: UUID
    candidate_id: Optional[UUID] = None
    agent_name: str
    opinion_type: PatchAgentOpinionType
    score: float
    confidence: float
    rationale: Optional[str] = None
    concerns_json: Dict[str, Any] = {}
    recommendation: Optional[str] = None
    created_at: datetime

class PatchNegotiationSessionSchema(BaseSchema):
    execution_id: UUID
    status: PatchNegotiationStatus
    started_at: datetime
    finished_at: Optional[datetime] = None
    participant_agents_json: Dict[str, Any] = {}
    candidate_count: int
    selected_candidate_id: Optional[UUID] = None
    consensus_score: float
    disagreement_score: float
    final_rationale: Optional[str] = None
    evidence_hash: Optional[str] = None
    created_at: datetime

class PatchDebateTurnSchema(BaseSchema):
    negotiation_session_id: UUID
    agent_name: str
    candidate_id: Optional[UUID] = None
    turn_type: PatchDebateTurnType
    message: str
    claims_json: Dict[str, Any] = {}
    evidence_refs_json: Dict[str, Any] = {}
    confidence: float
    created_at: datetime

class PatchCandidateScoreSchema(BaseSchema):
    candidate_id: UUID
    execution_id: UUID
    safety_score: float
    quality_score: float
    test_score: float
    cognitive_integrity_score: float
    policy_score: float
    cost_score: float
    maintainability_score: float
    rollback_safety_score: float
    total_score: float
    scoring_rationale: Optional[str] = None
    created_at: datetime

class PatchSelectionDecisionSchema(BaseSchema):
    execution_id: UUID
    negotiation_session_id: UUID
    selected_candidate_id: Optional[UUID] = None
    decision: PatchSelectionDecisionType
    reason: Optional[str] = None
    rejected_candidates_json: Dict[str, Any] = {}
    operator_visible_explanation: Optional[str] = None
    evidence_hash: Optional[str] = None
    created_at: datetime

class NegotiationStartRequest(BaseModel):
    execution_id: UUID
    agents: List[str] = []

class TraceRecordRequest(BaseModel):
    step_name: str
    status: str
    agent_name: Optional[str] = None
    cost_usd: float = 0.0
    token_input: int = 0
    token_output: int = 0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = {}

class UIKnowledgeNodeSchema(BaseSchema):
    id: UUID
    node_key: str
    node_type: str
    source_type: str
    source_id: Optional[str]
    tenant_key: Optional[str]
    project_key: Optional[str]
    cluster_key: Optional[str]
    title: str
    summary: Optional[str]
    severity: str
    confidence: float
    metadata: Dict[str, Any] = Field(alias="metadata_json")
    created_at: datetime
    updated_at: datetime

class UIKnowledgeEdgeSchema(BaseSchema):
    id: UUID
    source_node_key: str
    target_node_key: str
    edge_type: str
    confidence: float
    evidence_refs: List[str] = Field(alias="evidence_refs_json")
    metadata: Dict[str, Any] = Field(alias="metadata_json")
    created_at: datetime

class UICausalMemorySchema(BaseSchema):
    id: UUID
    memory_key: str
    pattern_type: str
    root_cause: str
    trigger_conditions: Dict[str, Any] = Field(alias="trigger_conditions_json")
    action_taken: Dict[str, Any] = Field(alias="action_taken_json")
    outcome: Dict[str, Any] = Field(alias="outcome_json")
    success_score: float
    recurrence_count: int
    confidence: float
    last_seen_at: datetime
    created_at: datetime
    updated_at: datetime

class UICausalChainSchema(BaseSchema):
    id: UUID
    chain_key: str
    incident_id: Optional[UUID]
    war_room_id: Optional[UUID]
    root_node_key: str
    terminal_node_key: str
    chain: List[Dict[str, Any]] = Field(alias="chain_json")
    causal_confidence: float
    summary: Optional[str]
    evidence_hash: Optional[str]
    created_at: datetime

class UIIncidentPatternSchema(BaseSchema):
    id: UUID
    pattern_key: str
    pattern_type: str
    affected_domain: str
    recurrence_count: int
    example_incidents: List[str] = Field(alias="example_incidents_json")
    common_root_causes: List[str] = Field(alias="common_root_causes_json")
    successful_remediations: List[str] = Field(alias="successful_remediations_json")
    failed_remediations: List[str] = Field(alias="failed_remediations_json")
    recommended_action: Optional[str]
    risk_level: str
    confidence: float
    created_at: datetime
    updated_at: datetime

class UISimilarCaseMatchSchema(BaseSchema):
    id: UUID
    query_source_type: str
    query_source_id: str
    matched_source_type: str
    matched_source_id: str
    similarity_score: float
    matched_features: List[str] = Field(alias="matched_features_json")
    recommended_action: Optional[str]
    confidence: float
    created_at: datetime

class UIRiskPredictionSchema(BaseSchema):
    id: UUID
    prediction_key: str
    target_type: str
    target_key: str
    risk_type: str
    probability: float
    severity: str
    predicted_window: str
    contributing_factors: List[str] = Field(alias="contributing_factors_json")
    recommended_prevention: Optional[str]
    status: str
    created_at: datetime

class UIKnowledgeGraphOverviewSchema(BaseSchema):
    total_nodes: int
    total_edges: int
    node_type_counts: Dict[str, int]
    edge_type_counts: Dict[str, int]
    last_rebuild_at: Optional[datetime]

class UIKnowledgeReportSchema(BaseSchema):
    id: UUID
    title: str
    period_start: datetime
    period_end: datetime
    summary_json: Dict[str, Any]
    key_findings_json: List[str]
    risk_predictions_json: List[Dict[str, Any]]
    evidence_hash: Optional[str]
    generated_at: datetime

class SimilarCaseRequest(BaseModel):
    source_type: str
    source_id: str
    limit: int = 5

# --- Phase 30: Final Integration + Production Hardening + Release Lock Schemas ---

class UIFinalIntegrationAuditSchema(BaseSchema):
    id: UUID
    audit_key: str
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    checked_modules: Dict[str, str] = Field(alias="checked_modules_json")
    failed_modules: List[str] = Field(alias="failed_modules_json")
    warnings: List[str] = Field(alias="warnings_json")
    summary: Dict[str, Any] = Field(alias="summary_json")
    evidence_hash: Optional[str]
    created_at: datetime

class UIReleaseReadinessCheckSchema(BaseSchema):
    id: UUID
    check_key: str
    category: str
    status: str
    score: float
    blockers: List[str] = Field(alias="blockers_json")
    warnings: List[str] = Field(alias="warnings_json")
    recommendation: Optional[str]
    created_at: datetime

class UIFinalAuditPackSchema(BaseSchema):
    id: UUID
    pack_key: str
    status: str
    generated_at: datetime
    version: str
    included_sections: List[str] = Field(alias="included_sections_json")
    residual_risks: List[Dict[str, Any]] = Field(alias="residual_risks_json")
    known_limitations: List[str] = Field(alias="known_limitations_json")
    summary: Dict[str, Any] = Field(alias="summary_json", default_factory=dict)
    evidence_hash: Optional[str]
    report_path: Optional[str]
    created_at: datetime

class UIReleaseLockSchema(BaseSchema):
    id: UUID
    release_key: str
    version: str
    status: str
    locked_by: str
    locked_at: datetime
    commit_sha: Optional[str]
    test_summary: Dict[str, Any] = Field(alias="test_summary_json")
    audit_pack_id: Optional[UUID]
    release_notes: Optional[str]
    evidence_hash: Optional[str]
    created_at: datetime

class UISmokeTestResultSchema(BaseModel):
    module_name: str
    status: str
    latency_ms: int
    error_message: Optional[str] = None
    last_run_at: datetime

class UIPhaseCompletionSchema(BaseModel):
    phase_id: int
    phase_name: str
    status: str
    completion_date: Optional[datetime]
    blockers_count: int
    warnings_count: int

class UIResidualRiskSchema(BaseModel):
    risk_id: str
    module: str
    severity: str
    description: str
    mitigation: str
    is_accepted: bool = False
    accepted_by: Optional[str] = None
    accepted_at: Optional[datetime] = None
    mitigation_strategy: str
    operator_rationale: Optional[str]
    status: str # ACCEPTED, MITIGATED, MONITORING
