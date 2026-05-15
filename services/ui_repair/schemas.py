from pydantic import BaseModel, Field
from enum import Enum
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

class UIPilotEventSchema(BaseSchema):
    id: str
    rollout_id: str
    event_type: str
    route: Optional[str] = None
    case_id: Optional[str] = None
    attempt_id: Optional[str] = None
    severity: str = "INFO"
    decision: Optional[str] = None
    payload_json: Dict[str, Any] = {}
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

class UIOperatorActionLedgerSchema(BaseSchema):
    id: str
    rollout_id: str
    operator: str
    action_type: str
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    rationale: str
    before_state_json: Dict[str, Any] = {}
    after_state_json: Dict[str, Any] = {}
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
