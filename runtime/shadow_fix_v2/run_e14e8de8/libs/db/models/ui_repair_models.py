import enum
import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from libs.db.base import GUID, Base, SmartJSON, utcnow


class FailureType(str, enum.Enum):
    BLANK_PAGE = "BLANK_PAGE"
    ROUTE_404 = "ROUTE_404"
    API_404 = "API_404"
    API_500 = "API_500"
    CONSOLE_ERROR = "CONSOLE_ERROR"
    HYDRATION_ERROR = "HYDRATION_ERROR"
    REDIRECT_LOOP = "REDIRECT_LOOP"
    NETWORK_FAILURE = "NETWORK_FAILURE"
    LAYOUT_COLLAPSE = "LAYOUT_COLLAPSE"
    TIMEOUT = "TIMEOUT"
    UNKNOWN = "UNKNOWN"

class UIRepairStatus(str, enum.Enum):
    DETECTED = "DETECTED"
    EVIDENCE_CAPTURED = "EVIDENCE_CAPTURED"
    CLASSIFIED = "CLASSIFIED"
    DIAGNOSTIC_LINKED = "DIAGNOSTIC_LINKED"
    READY_FOR_STAGEHAND = "READY_FOR_STAGEHAND"
    REPAIRING = "REPAIRING"
    PATCH_GENERATED = "PATCH_GENERATED"
    PR_OPENED = "PR_OPENED"
    WAITING_GOVERNANCE = "WAITING_GOVERNANCE"
    APPLYING = "APPLYING"
    REPAIR_FAILED = "REPAIR_FAILED"
    MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"
    RESOLVED = "RESOLVED"
    IGNORED = "IGNORED"

class RepairAttemptStatus(str, enum.Enum):
    STARTED = "STARTED"
    STAGEHAND_RUNNING = "STAGEHAND_RUNNING"
    STAGEHAND_COMPLETED = "STAGEHAND_COMPLETED"
    STAGEHAND_FAILED = "STAGEHAND_FAILED"
    OPEN_SWE_QUEUED = "OPEN_SWE_QUEUED"
    OPEN_SWE_RUNNING = "OPEN_SWE_RUNNING"
    PATCH_GENERATED = "PATCH_GENERATED"
    PR_OPENED = "PR_OPENED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    WAITING_GOVERNANCE = "WAITING_GOVERNANCE"
    REVIEW_RUNNING = "REVIEW_RUNNING"
    VERIFIER_RUNNING = "VERIFIER_RUNNING"
    GOVERNANCE_PENDING = "GOVERNANCE_PENDING"
    APPLYING = "APPLYING"
    APPLIED = "APPLIED"

class PRReviewStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"

class VerifierStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"
    SKIPPED = "SKIPPED"
    TIMEOUT = "TIMEOUT"

class GovernanceApprovalStatus(str, enum.Enum):
    NOT_REQUESTED = "NOT_REQUESTED"
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class UIRepairSeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class RedTeamScenarioType(str, enum.Enum):
    TENANT_ISOLATION_PROBE = "TENANT_ISOLATION_PROBE"
    IDENTITY_REPLAY_PROBE = "IDENTITY_REPLAY_PROBE"
    CAPABILITY_TOKEN_ABUSE = "CAPABILITY_TOKEN_ABUSE"
    POLICY_BYPASS_ATTEMPT = "POLICY_BYPASS_ATTEMPT"
    TOOL_GOVERNANCE_ABUSE = "TOOL_GOVERNANCE_ABUSE"
    MCP_WRITE_ABUSE = "MCP_WRITE_ABUSE"
    SECRET_EXFILTRATION_SIMULATION = "SECRET_EXFILTRATION_SIMULATION"
    COGNITIVE_HALLUCINATION_INJECTION = "COGNITIVE_HALLUCINATION_INJECTION"
    EVIDENCE_TAMPERING_SIMULATION = "EVIDENCE_TAMPERING_SIMULATION"
    GOVERNANCE_APPROVAL_BYPASS = "GOVERNANCE_APPROVAL_BYPASS"
    COST_EXHAUSTION_SIMULATION = "COST_EXHAUSTION_SIMULATION"
    MESH_FAILOVER_ABUSE = "MESH_FAILOVER_ABUSE"
    CRISIS_MODE_MISUSE = "CRISIS_MODE_MISUSE"

class GuardrailTuningStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SIMULATED = "SIMULATED"
    REGRESSION_PASSED = "REGRESSION_PASSED"
    REGRESSION_FAILED = "REGRESSION_FAILED"
    CANARY_RUNNING = "CANARY_RUNNING"
    CANARY_PASSED = "CANARY_PASSED"
    CANARY_FAILED = "CANARY_FAILED"
    GOVERNANCE_REQUESTED = "GOVERNANCE_REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    APPLIED = "APPLIED"
    ROLLED_BACK = "ROLLED_BACK"
    MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"

class GuardrailDomain(str, enum.Enum):
    TENANT_ISOLATION = "TENANT_ISOLATION"
    IDENTITY = "IDENTITY"
    POLICY_AS_CODE = "POLICY_AS_CODE"
    TOOL_GOVERNANCE = "TOOL_GOVERNANCE"
    MCP_GOVERNANCE = "MCP_GOVERNANCE"
    COGNITIVE_INTEGRITY = "COGNITIVE_INTEGRITY"
    SECURITY_POSTURE = "SECURITY_POSTURE"
    BUDGET_GUARD = "BUDGET_GUARD"
    LIVE_SAFETY_GUARD = "LIVE_SAFETY_GUARD"
    EVIDENCE_LEDGER = "EVIDENCE_LEDGER"
    RESILIENCY_MESH = "RESILIENCY_MESH"
    REMEDIATION_LOOP_ABUSE = "REMEDIATION_LOOP_ABUSE"

class RedTeamTargetDomain(str, enum.Enum):
    IDENTITY = "IDENTITY"
    POLICY = "POLICY"
    TENANT_ISOLATION = "TENANT_ISOLATION"
    TOOL_GOVERNANCE = "TOOL_GOVERNANCE"
    MCP = "MCP"
    EVIDENCE = "EVIDENCE"
    COGNITIVE_INTEGRITY = "COGNITIVE_INTEGRITY"
    GOVERNANCE = "GOVERNANCE"
    FINOPS = "FINOPS"
    RESILIENCY_MESH = "RESILIENCY_MESH"
    SECURITY_POSTURE = "SECURITY_POSTURE"
    REMEDIATION = "REMEDIATION"

class RedTeamSafetyMode(str, enum.Enum):
    SIMULATION_ONLY = "SIMULATION_ONLY"
    DRY_RUN = "DRY_RUN"
    SANDBOX = "SANDBOX"
    NON_DESTRUCTIVE_LIVE_CHECK = "NON_DESTRUCTIVE_LIVE_CHECK"

class RedTeamRunStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    BLOCKED_BY_SAFETY = "BLOCKED_BY_SAFETY"
    CANCELLED = "CANCELLED"
    MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"

class AdversarialDriftType(str, enum.Enum):
    DECISION_DRIFT = "DECISION_DRIFT"
    POLICY_DRIFT_UNDER_ATTACK = "POLICY_DRIFT_UNDER_ATTACK"
    TRUST_SCORE_DRIFT = "TRUST_SCORE_DRIFT"
    EVIDENCE_CHAIN_DRIFT = "EVIDENCE_CHAIN_DRIFT"
    TOOL_DECISION_DRIFT = "TOOL_DECISION_DRIFT"
    COGNITIVE_INTEGRITY_DRIFT = "COGNITIVE_INTEGRITY_DRIFT"
    COST_POLICY_DRIFT = "COST_POLICY_DRIFT"
    TENANT_SCOPE_DRIFT = "TENANT_SCOPE_DRIFT"

class IncidentSeverity(str, enum.Enum):
    P0_CRITICAL = "P0_CRITICAL"
    P1_HIGH = "P1_HIGH"
    P2_MEDIUM = "P2_MEDIUM"
    P3_LOW = "P3_LOW"

class WarRoomStatus(str, enum.Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    MITIGATING = "MITIGATING"
    WAITING_GOVERNANCE = "WAITING_GOVERNANCE"
    WAITING_OPERATOR = "WAITING_OPERATOR"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    ESCALATED = "ESCALATED"

class IncidentSource(str, enum.Enum):
    SECURITY_POSTURE_FINDING = "SECURITY_POSTURE_FINDING"
    RED_TEAM_FINDING = "RED_TEAM_FINDING"
    COGNITIVE_INTEGRITY_BLOCK = "COGNITIVE_INTEGRITY_BLOCK"
    IDENTITY_VIOLATION = "IDENTITY_VIOLATION"
    TOOL_POLICY_VIOLATION = "TOOL_POLICY_VIOLATION"
    TENANT_ISOLATION_VIOLATION = "TENANT_ISOLATION_VIOLATION"
    MESH_FAILOVER = "MESH_FAILOVER"
    SLO_BREACH = "SLO_BREACH"
    COST_ANOMALY = "COST_ANOMALY"
    GOVERNANCE_BYPASS_ATTEMPT = "GOVERNANCE_BYPASS_ATTEMPT"
    EVIDENCE_CHAIN_FAILURE = "EVIDENCE_CHAIN_FAILURE"
    REMEDIATION_FAILURE = "REMEDIATION_FAILURE"

class UISmokeRun(Base):
    """Log record for a complete UI smoke test run."""
    __tablename__ = "ui_smoke_runs"

    id           = Column(GUID, primary_key=True, default=uuid.uuid4)
    status       = Column(String(32), default="RUNNING") # RUNNING | COMPLETED | FAILED
    total_routes = Column(Integer, default=0)
    passed_routes= Column(Integer, default=0)
    failed_routes= Column(Integer, default=0)
    started_at   = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    finished_at  = Column(DateTime(timezone=True))
    report_path  = Column(String(512))
    summary_json = Column(SmartJSON(), default=dict)

class UIRouteHealth(Base):
    """Health matrix for each tracked UI route."""
    __tablename__ = "ui_route_health"

    id               = Column(GUID, primary_key=True, default=uuid.uuid4)
    route            = Column(String(256), nullable=False, unique=True, index=True)
    last_status      = Column(String(32)) # PASS | FAIL
    last_http_status = Column(Integer)
    last_checked_at  = Column(DateTime(timezone=True))
    last_success_at  = Column(DateTime(timezone=True))
    failure_count    = Column(Integer, default=0)
    avg_response_ms  = Column(Float, default=0.0)

    blank_page_detected = Column(Boolean, default=False)
    console_error_count = Column(Integer, default=0)
    network_error_count = Column(Integer, default=0)

    last_case_id     = Column(GUID, nullable=True)

class UIRepairCase(Base):
    """A specific UI failure case with captured evidence."""
    __tablename__ = "ui_repair_cases"

    id           = Column(GUID, primary_key=True, default=uuid.uuid4)
    route        = Column(String(256), nullable=False, index=True)
    title        = Column(String(512))
    status       = Column(String(32), default="DETECTED", index=True) # UIRepairStatus
    severity     = Column(String(32), default="MEDIUM", index=True)   # UIRepairSeverity
    failure_type = Column(String(32), default="UNKNOWN", index=True)  # FailureType

    tenant_key   = Column(String(64), index=True)
    cluster_key  = Column(String(64), index=True)
    project_key  = Column(String(64), index=True)

    http_status          = Column(Integer)
    blank_page_detected  = Column(Boolean, default=False)
    console_errors_json  = Column(SmartJSON(), default=list)
    network_errors_json  = Column(SmartJSON(), default=list)
    hydration_errors_json= Column(SmartJSON(), default=list)
    redirect_chain_json  = Column(SmartJSON(), default=list)

    screenshot_path      = Column(String(512))
    trace_path           = Column(String(512))
    evidence_json_path   = Column(String(512))
    patch_path           = Column(String(512))
    pr_url               = Column(String(512))
    repair_summary       = Column(Text)

    suspected_area       = Column(String(256))

    linked_workflow_id           = Column(GUID, nullable=True)
    linked_incident_id           = Column(GUID, nullable=True)
    linked_runtime_diagnostic_id = Column(String(64), nullable=True)
    linked_evidence_id           = Column(GUID, nullable=True)

    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    attempts = relationship("UIRepairAttempt", back_populates="case", cascade="all, delete-orphan")
    events   = relationship("UIRepairEvent", back_populates="case", cascade="all, delete-orphan")

class UIRepairAttempt(Base):
    """Detailed log of a single autonomous repair attempt."""
    __tablename__ = "ui_repair_attempts"

    id         = Column(GUID, primary_key=True, default=uuid.uuid4)
    case_id    = Column(GUID, ForeignKey("ui_repair_cases.id"), nullable=False, index=True)
    attempt_no = Column(Integer, default=1)
    status     = Column(String(32), default="STARTED", index=True) # RepairAttemptStatus

    started_at  = Column(DateTime(timezone=True), default=utcnow)
    finished_at = Column(DateTime(timezone=True))

    stagehand_status    = Column(String(32))
    open_swe_status     = Column(String(32))

    stagehand_summary_json = Column(SmartJSON(), default=dict)
    diagnostic_brief_json  = Column(SmartJSON(), default=dict)
    suspected_files_json   = Column(SmartJSON(), default=list)
    repair_instruction     = Column(Text)

    patch_path    = Column(String(512))
    patch_summary = Column(Text)
    pr_url        = Column(String(512))
    error_message = Column(Text)
    evidence_path = Column(String(512))

    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    case = relationship("UIRepairCase", back_populates="attempts")
    events = relationship("UIRepairEvent", back_populates="attempt", cascade="all, delete-orphan")

class UIRepairEvent(Base):
    """Event log for UI repair process tracking."""
    __tablename__ = "ui_repair_events"

    id         = Column(GUID, primary_key=True, default=uuid.uuid4)
    case_id    = Column(GUID, ForeignKey("ui_repair_cases.id"), nullable=False, index=True)
    attempt_id = Column(GUID, ForeignKey("ui_repair_attempts.id"), nullable=True, index=True)

    event_type = Column(String(64), nullable=False, index=True)
    status     = Column(String(32))
    message    = Column(Text)
    payload_json = Column(SmartJSON(), default=dict)

    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    case = relationship("UIRepairCase", back_populates="events")
    attempt = relationship("UIRepairAttempt", back_populates="events")

class UIRepairPRReview(Base):
    """PR-Agent automated review results for a repair attempt."""
    __tablename__ = "ui_repair_pr_reviews"

    id         = Column(GUID, primary_key=True, default=uuid.uuid4)
    case_id    = Column(GUID, ForeignKey("ui_repair_cases.id"), nullable=False, index=True)
    attempt_id = Column(GUID, ForeignKey("ui_repair_attempts.id"), nullable=False, index=True)

    pr_url   = Column(String(512))
    provider = Column(String(64), default="PR_AGENT")
    status   = Column(String(32), default="PENDING") # PRReviewStatus

    review_summary       = Column(Text)
    describe_output_json = Column(SmartJSON(), default=dict)
    review_output_json   = Column(SmartJSON(), default=dict)
    improve_output_json  = Column(SmartJSON(), default=dict)
    changed_files_json   = Column(SmartJSON(), default=list)
    risk_level           = Column(String(32)) # LOW | MEDIUM | HIGH

    blocking_findings_json   = Column(SmartJSON(), default=list)
    suggestions_json         = Column(SmartJSON(), default=list)
    governance_warnings_json = Column(SmartJSON(), default=list)
    raw_output_path          = Column(String(512))

    started_at  = Column(DateTime(timezone=True))
    finished_at = Column(DateTime(timezone=True))
    created_at  = Column(DateTime(timezone=True), default=utcnow)
    updated_at  = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class UIRepairVerifierRun(Base):
    """Build, lint, and test gate results for a repair attempt."""
    __tablename__ = "ui_repair_verifier_runs"

    id         = Column(GUID, primary_key=True, default=uuid.uuid4)
    case_id    = Column(GUID, ForeignKey("ui_repair_cases.id"), nullable=False, index=True)
    attempt_id = Column(GUID, ForeignKey("ui_repair_attempts.id"), nullable=False, index=True)

    pr_url = Column(String(512))
    status = Column(String(32), default="PENDING") # VerifierStatus

    lint_status             = Column(String(32))
    typecheck_status        = Column(String(32))
    build_status            = Column(String(32))
    unit_test_status        = Column(String(32))
    playwright_status       = Column(String(32))
    smoke_status            = Column(String(32))
    route_regression_status = Column(String(32))

    result_summary_json = Column(SmartJSON(), default=dict)
    logs_path           = Column(String(512))

    started_at  = Column(DateTime(timezone=True))
    finished_at = Column(DateTime(timezone=True))
    created_at  = Column(DateTime(timezone=True), default=utcnow)
    updated_at  = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class UIRepairGovernanceApproval(Base):
    """Formal governance approval record for a UI repair."""
    __tablename__ = "ui_repair_governance_approvals"

    id         = Column(GUID, primary_key=True, default=uuid.uuid4)
    case_id    = Column(GUID, ForeignKey("ui_repair_cases.id"), nullable=False, index=True)
    attempt_id = Column(GUID, ForeignKey("ui_repair_attempts.id"), nullable=False, index=True)

    pr_url              = Column(String(512))
    approval_request_id = Column(String(64))
    status              = Column(String(32), default="NOT_REQUESTED") # GovernanceApprovalStatus

    risk_level                 = Column(String(32))
    auto_apply_allowed         = Column(Boolean, default=False)
    requires_operator_approval = Column(Boolean, default=True)
    requires_pr_agent_review   = Column(Boolean, default=True)
    requires_verifier_mesh     = Column(Boolean, default=True)

    policy_decision_json = Column(SmartJSON(), default=dict)

    approved_by      = Column(String(128))
    approved_at      = Column(DateTime(timezone=True))
    rejected_by      = Column(String(128))
    rejected_at      = Column(DateTime(timezone=True))
    rejection_reason = Column(Text)

    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class UIRepairApplyResult(Base):
    """The outcome of applying/merging the repair patch."""
    __tablename__ = "ui_repair_apply_results"

    id         = Column(GUID, primary_key=True, default=uuid.uuid4)
    case_id    = Column(GUID, ForeignKey("ui_repair_cases.id"), nullable=False, index=True)
    attempt_id = Column(GUID, ForeignKey("ui_repair_attempts.id"), nullable=False, index=True)

    pr_url = Column(String(512))
    status = Column(String(32), default="PENDING") # SUCCESS | FAILED

    apply_mode            = Column(String(64)) # GIT_APPLY | PR_MERGE
    merge_commit_sha      = Column(String(128))
    rollback_snapshot_path = Column(String(512))

    applied_at    = Column(DateTime(timezone=True))
    applied_by    = Column(String(128))
    error_message = Column(Text)

    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class UIMonitoringConfig(Base):
    """Configuration for 24/7 continuous UI monitoring and autonomous self-healing."""
    __tablename__ = "ui_monitoring_config"

    id               = Column(GUID, primary_key=True, default=uuid.uuid4)
    enabled          = Column(Boolean, default=True)
    interval_seconds = Column(Integer, default=3600) # Default: 1 hour
    route_scope_json = Column(SmartJSON(), default=list)

    auto_repair_enabled        = Column(Boolean, default=False)
    auto_repair_risk_threshold = Column(String(32), default="LOW")
    max_repairs_per_hour       = Column(Integer, default=1)
    max_repairs_per_day        = Column(Integer, default=5)
    cooldown_minutes           = Column(Integer, default=30)

    notify_on_failure           = Column(Boolean, default=True)
    notify_on_repair_started    = Column(Boolean, default=True)
    notify_on_governance_waiting = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class UIMonitoringRun(Base):
    """Audit record for a scheduled monitoring/smoke execution."""
    __tablename__ = "ui_monitoring_runs"

    id           = Column(GUID, primary_key=True, default=uuid.uuid4)
    status       = Column(String(32), default="PENDING") # PENDING | RUNNING | COMPLETED | FAILED
    triggered_by = Column(String(64), default="SCHEDULED") # SCHEDULED | MANUAL | EVENT

    started_at  = Column(DateTime(timezone=True), default=utcnow)
    finished_at = Column(DateTime(timezone=True))

    total_routes              = Column(Integer, default=0)
    passed_routes             = Column(Integer, default=0)
    failed_routes             = Column(Integer, default=0)
    degraded_routes           = Column(Integer, default=0)

    auto_repair_started_count = Column(Integer, default=0)
    cases_created_count       = Column(Integer, default=0)
    cases_updated_count       = Column(Integer, default=0)

    report_path  = Column(String(512))
    summary_json = Column(SmartJSON(), default=dict)

    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class UIRouteHealthHist(Base):
    """Historical data points for UI route health tracking and trend analysis."""
    __tablename__ = "ui_route_health_hist"

    id               = Column(GUID, primary_key=True, default=uuid.uuid4)
    route_id         = Column(GUID, ForeignKey("ui_route_health.id"), nullable=False, index=True)
    monitoring_run_id = Column(GUID, ForeignKey("ui_monitoring_runs.id"), nullable=True, index=True)

    route            = Column(String(256), nullable=False, index=True)
    status           = Column(String(32)) # PASS | FAIL
    http_status      = Column(Integer)
    response_time_ms = Column(Float)

    captured_at = Column(DateTime(timezone=True), default=utcnow, index=True)

class UIChaosDrillScenario(Base):
    """Controlled failure scenarios for UI resilience testing."""
    __tablename__ = "ui_chaos_drill_scenarios"

    id               = Column(GUID, primary_key=True, default=uuid.uuid4)
    name             = Column(String(128), nullable=False)
    description      = Column(Text)
    failure_type     = Column(String(64), nullable=False) # BLANK_PAGE_INJECTION, etc.
    target_route     = Column(String(256))
    target_component = Column(String(128))
    target_api       = Column(String(256))

    expected_detection      = Column(String(64)) # e.g., "BLANK_PAGE"
    expected_severity       = Column(String(32)) # LOW | MEDIUM | HIGH | CRITICAL
    expected_policy_decision = Column(String(64)) # AUTO_REPAIR | MANUAL_REQUIRED
    expected_repair_level    = Column(String(64)) # CODE_PATCH | REFRESH_ONLY
    expected_governance_behavior = Column(String(64)) # OPERATOR_APPROVAL_REQUIRED

    is_enabled        = Column(Boolean, default=True)
    is_destructive    = Column(Boolean, default=False)
    requires_sandbox  = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class UIChaosDrillRun(Base):
    """Execution record for a chaos drill."""
    __tablename__ = "ui_chaos_drill_runs"

    id          = Column(GUID, primary_key=True, default=uuid.uuid4)
    scenario_id = Column(GUID, ForeignKey("ui_chaos_drill_scenarios.id"), nullable=False)
    status      = Column(String(32), default="PENDING") # PENDING | RUNNING | PASSED | FAILED | BLOCKED_BY_SAFETY

    started_at  = Column(DateTime(timezone=True), default=utcnow)
    finished_at = Column(DateTime(timezone=True))
    triggered_by = Column(String(128))
    environment  = Column(String(64)) # sandbox | production

    target_route         = Column(String(256))
    injected_failure_type = Column(String(64))
    detection_status      = Column(String(32)) # DETECTED | MISSED
    detected_failure_type = Column(String(64))
    detected_severity     = Column(String(32))

    repair_case_id         = Column(GUID, ForeignKey("ui_repair_cases.id"), nullable=True)
    monitoring_run_id      = Column(GUID, ForeignKey("ui_monitoring_runs.id"), nullable=True)
    repair_attempt_id      = Column(GUID, nullable=True) # UUID
    policy_decision_id     = Column(String(128))
    governance_approval_id = Column(GUID, nullable=True)

    passed         = Column(Boolean, default=False)
    failure_reason = Column(Text)
    summary_json   = Column(SmartJSON(), default=dict)
    evidence_path  = Column(String(512))

    created_at = Column(DateTime(timezone=True), default=utcnow)

class UISoakValidationRun(Base):
    """Long-term stability and soak testing record for the monitoring loop."""
    __tablename__ = "ui_soak_validation_runs"

    id          = Column(GUID, primary_key=True, default=uuid.uuid4)
    status      = Column(String(32), default="PENDING") # RUNNING | COMPLETED | FAILED
    started_at  = Column(DateTime(timezone=True), default=utcnow)
    finished_at = Column(DateTime(timezone=True))

    duration_minutes = Column(Integer, default=60)
    monitoring_runs_count = Column(Integer, default=0)
    total_routes_checked  = Column(Integer, default=0)
    total_failures_detected = Column(Integer, default=0)
    total_cases_created    = Column(Integer, default=0)
    total_auto_repairs_started = Column(Integer, default=0)
    total_governance_requests  = Column(Integer, default=0)

    false_positive_count    = Column(Integer, default=0)
    false_negative_count    = Column(Integer, default=0)
    worker_errors_count     = Column(Integer, default=0)
    scheduler_skips_count   = Column(Integer, default=0)

    memory_growth_mb        = Column(Float, default=0.0)
    avg_monitoring_latency_s = Column(Float, default=0.0)

    summary_json = Column(SmartJSON(), default=dict)
    report_path  = Column(String(512))

    created_at = Column(DateTime(timezone=True), default=utcnow)

class UIRecoveryProofPack(Base):
    """A consolidated report proving recovery and resilience capabilities."""
    __tablename__ = "ui_recovery_proof_packs"

    id        = Column(GUID, primary_key=True, default=uuid.uuid4)
    pack_name = Column(String(128), nullable=False)
    status    = Column(String(32), default="GENERATING") # READY | FAILED

    generated_at = Column(DateTime(timezone=True), default=utcnow)
    period_start = Column(DateTime(timezone=True))
    period_end   = Column(DateTime(timezone=True))

    drill_run_ids_json      = Column(SmartJSON(), default=list)
    soak_run_ids_json       = Column(SmartJSON(), default=list)
    monitoring_run_ids_json = Column(SmartJSON(), default=list)
    repair_case_ids_json    = Column(SmartJSON(), default=list)

    evidence_hash     = Column(String(128))
    report_path       = Column(String(512))
    executive_summary = Column(Text)

    created_at = Column(DateTime(timezone=True), default=utcnow)

# --- Phase 9: Advanced Failure Injection & Escalation Models ---

class UIAdvancedChaosScenario(Base):
    """Advanced chaos scenarios including network and browser level disruptions."""
    __tablename__ = "ui_advanced_chaos_scenarios"

    id          = Column(GUID, primary_key=True, default=uuid.uuid4)
    name        = Column(String(128), nullable=False)
    description = Column(Text)

    chaos_type  = Column(String(64), nullable=False) # Enum: NETWORK_LATENCY, JS_CHUNK_BLOCK, etc.
    target_route = Column(String(256))
    target_api   = Column(String(256))
    target_resource = Column(String(256)) # pattern for resource blocking

    injection_mode     = Column(String(32), default="SYNTHETIC") # SYNTHETIC | MOCK | INTERCEPT
    expected_detection = Column(String(64)) # FailureType expected
    expected_severity  = Column(String(32))

    requires_sandbox   = Column(Boolean, default=True)
    is_destructive     = Column(Boolean, default=False)
    max_duration_seconds = Column(Integer, default=300)

    is_enabled  = Column(Boolean, default=True)
    created_at  = Column(DateTime(timezone=True), default=utcnow)
    updated_at  = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class UIAdvancedChaosRun(Base):
    """Execution records for advanced chaos drills."""
    __tablename__ = "ui_advanced_chaos_runs"

    id          = Column(GUID, primary_key=True, default=uuid.uuid4)
    scenario_id = Column(GUID, ForeignKey("ui_advanced_chaos_scenarios.id"))
    status      = Column(String(32), default="RUNNING") # RUNNING | COMPLETED | FAILED | CLEANUP_FAILED

    chaos_type  = Column(String(64))
    target_route = Column(String(256))

    started_at  = Column(DateTime(timezone=True), default=utcnow)
    finished_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)

    # Injection Params
    injected_latency_ms = Column(Integer, default=0)
    injected_timeout_ms = Column(Integer, default=0)
    blocked_resource_pattern = Column(String(256))
    websocket_disconnected = Column(Boolean, default=False)
    cache_stale = Column(Boolean, default=False)

    # Detection results
    detected_by_monitoring = Column(Boolean, default=False)
    detected_failure_type  = Column(String(64))
    detected_severity     = Column(String(32))
    policy_decision       = Column(String(64))

    repair_case_id          = Column(GUID, ForeignKey("ui_repair_cases.id"), nullable=True)
    operational_incident_id = Column(GUID, nullable=True) # Linked incident if critical

    evidence_path  = Column(String(512))
    cleanup_status = Column(String(32), default="PENDING") # PENDING | SUCCESS | FAILED

    passed         = Column(Boolean, default=False)
    failure_reason = Column(Text)
    summary_json   = Column(SmartJSON(), default=dict)

    created_at  = Column(DateTime(timezone=True), default=utcnow)

class UIOperatorEscalation(Base):
    """Formal escalation of critical UI failures to human operators."""
    __tablename__ = "ui_operator_escalations"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    source_type: Mapped[str] = mapped_column(String(64)) # MONITORING | CHAOS | AUTO_REPAIR_FAILURE
    source_id: Mapped[uuid.UUID] = mapped_column(GUID) # Case ID or Run ID

    route: Mapped[str] = mapped_column(String(256))
    severity: Mapped[str] = mapped_column(String(32)) # INFO | WATCH | OPERATOR_REVIEW | URGENT | CRITICAL | CRISIS
    escalation_level: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(32), default="OPEN") # OPEN | NOTIFIED | ACKNOWLEDGED | IN_PROGRESS | RESOLVED | SUPPRESSED | ESCALATED | FAILED_TO_NOTIFY

    reason: Mapped[str] = mapped_column(Text)
    assigned_to: Mapped[str | None] = mapped_column(String(128)) # User ID or Team

    notification_channels_json: Mapped[list[str]] = mapped_column(SmartJSON(), default=list) # ['DASHBOARD', 'EMAIL', 'TELEGRAM']
    notification_status_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict) # { 'EMAIL': 'SENT', 'TELEGRAM': 'FAILED' }

    acknowledged_by: Mapped[str | None] = mapped_column(String(128))
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_by: Mapped[str | None] = mapped_column(String(128))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class UINotificationDelivery(Base):
    """Tracking individual notification delivery attempts."""
    __tablename__ = "ui_notification_deliveries"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    escalation_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("ui_operator_escalations.id"))

    channel: Mapped[str] = mapped_column(String(32)) # DASHBOARD | EMAIL | TELEGRAM | SLACK
    status: Mapped[str] = mapped_column(String(32)) # PENDING | SENT | FAILED | RETRYING
    recipient: Mapped[str] = mapped_column(String(256))

    title: Mapped[str] = mapped_column(String(256))
    message_summary: Mapped[str] = mapped_column(Text)
    provider_response_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)

    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UICrisisControlState(Base):
    """Global switch for UI repair operational modes during crises."""
    __tablename__ = "ui_crisis_control_states"

    id          = Column(GUID, primary_key=True, default=uuid.uuid4)
    mode        = Column(String(64), default="NORMAL") # NORMAL | MONITOR_ONLY | SELF_HEALING_FROZEN | AUTO_REPAIR_FROZEN | FULL_UI_REPAIR_FREEZE | CRISIS_RESPONSE

    self_healing_frozen = Column(Boolean, default=False)
    monitoring_frozen   = Column(Boolean, default=False)
    auto_repair_frozen  = Column(Boolean, default=False)

    reason      = Column(Text)
    activated_by = Column(String(128))
    activated_at = Column(DateTime(timezone=True), default=utcnow)

    deactivated_by = Column(String(128))
    deactivated_at = Column(DateTime(timezone=True))

    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

# --- Phase 10: Final Enterprise Readiness & Release Gate Models ---

# --- Phase 10 Red Team placeholders removed in favor of Phase 24 consolidation ---


# --- Phase 10 Red Team runs removed in favor of Phase 24 operations ---


class UIEnterpriseReadinessAssessment(Base):
    """Holistic scoring of the UI repair system for enterprise production."""
    __tablename__ = "ui_enterprise_readiness_assessments"

    id          = Column(GUID, primary_key=True, default=uuid.uuid4)
    overall_score = Column(Float) # 0-100
    rating       = Column(String(32)) # Enterprise Ready, Pilot Only, etc.

    # Detailed scores
    monitoring_score     = Column(Float)
    governance_score     = Column(Float)
    resilience_score     = Column(Float)
    audit_score          = Column(Float)
    operations_score     = Column(Float)

    assessment_json      = Column(SmartJSON(), default=dict) # Breakdowns
    blocker_list_json    = Column(SmartJSON(), default=list)
    warning_list_json    = Column(SmartJSON(), default=list)

    assessed_by = Column(String(128))
    created_at  = Column(DateTime(timezone=True), default=utcnow)

class UIReleaseGateDecision(Base):
    """Final GO/NO-GO decisions for production release."""
    __tablename__ = "ui_release_gate_decisions"

    id          = Column(GUID, primary_key=True, default=uuid.uuid4)
    assessment_id = Column(GUID, ForeignKey("ui_enterprise_readiness_assessments.id"))

    decision    = Column(String(32)) # GO | GO_WITH_WARNINGS | PILOT_ONLY | NO_GO
    rationale   = Column(Text)

    gate_conditions_json = Column(SmartJSON(), default=dict) # passed/failed gates

    approver    = Column(String(128))
    decided_at  = Column(DateTime(timezone=True), default=utcnow)



class UIOperatorHandoverReport(Base):
    """Operational documentation for human-in-the-loop takeover."""
    __tablename__ = "ui_operator_handover_reports"

    id          = Column(GUID, primary_key=True, default=uuid.uuid4)
    title       = Column(String(256))

    architecture_summary = Column(Text)
    operational_guide    = Column(Text)
    emergency_protocols  = Column(Text)

    residual_risks_json  = Column(SmartJSON(), default=list)
    limitations_json     = Column(SmartJSON(), default=list)

    report_path = Column(String(512))
    created_at  = Column(DateTime(timezone=True), default=utcnow)

# Phase 11: Controlled Enterprise Pilot Rollout + Live Shadow Mode Models

class UIPilotRollout(Base):
    __tablename__ = "ui_pilot_rollouts"

    id = Column(String(64), primary_key=True)
    name = Column(String(255), nullable=False)
    status = Column(String(32), default="NOT_STARTED")  # NOT_STARTED, RUNNING, PAUSED, COMPLETED, FAILED, CANCELLED
    mode = Column(String(32), default="SHADOW_ONLY")   # SHADOW_ONLY, ASSISTED_REPAIR, GOVERNED_REPAIR, LIMITED_PRODUCTION
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    duration_days = Column(Integer, default=7)
    route_scope_json = Column(SmartJSON(), default=list)
    automation_level = Column(String(32), default="LOW")
    auto_apply_enabled = Column(Boolean, default=False)
    operator_approval_required = Column(Boolean, default=True)
    safety_policy_json = Column(SmartJSON(), default=dict)
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow)

    events = relationship("UIPilotEvent", back_populates="rollout", cascade="all, delete-orphan")
    metrics = relationship("UIPilotMetrics", back_populates="rollout", uselist=False, cascade="all, delete-orphan")
    ledger_entries = relationship("UIOperatorActionLedger", back_populates="rollout", cascade="all, delete-orphan")
    final_report = relationship("UIPilotFinalReport", back_populates="rollout", uselist=False, cascade="all, delete-orphan")

class UIPilotEvent(Base):
    __tablename__ = "ui_pilot_events"

    id = Column(String(64), primary_key=True)
    rollout_id = Column(String(64), ForeignKey("ui_pilot_rollouts.id"), nullable=False)
    event_type = Column(String(64), nullable=False)
    route = Column(String(512), nullable=True)
    case_id = Column(String(64), nullable=True)
    attempt_id = Column(String(64), nullable=True)
    severity = Column(String(32), default="INFO")
    decision = Column(String(32), nullable=True)
    payload_json = Column(SmartJSON(), default=dict)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    rollout = relationship("UIPilotRollout", back_populates="events")

class UIPilotMetrics(Base):
    __tablename__ = "ui_pilot_metrics"

    id = Column(String(64), primary_key=True)
    rollout_id = Column(String(64), ForeignKey("ui_pilot_rollouts.id"), nullable=False)
    monitoring_runs = Column(Integer, default=0)
    failures_detected = Column(Integer, default=0)
    repair_cases_created = Column(Integer, default=0)
    auto_diagnostics_started = Column(Integer, default=0)
    prs_created = Column(Integer, default=0)
    pr_agent_reviews = Column(Integer, default=0)
    verifier_runs = Column(Integer, default=0)
    governance_requests = Column(Integer, default=0)
    approved_applies = Column(Integer, default=0)
    rejected_repairs = Column(Integer, default=0)
    rollbacks = Column(Integer, default=0)
    false_positive_count = Column(Integer, default=0)
    false_negative_count = Column(Integer, default=0)
    avg_mttr_s = Column(Float, default=0.0)
    avg_governance_latency_s = Column(Float, default=0.0)
    operator_actions_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow)

    rollout = relationship("UIPilotRollout", back_populates="metrics")

class UIOperatorActionLedger(Base):
    __tablename__ = "ui_operator_action_ledger"

    id = Column(String(64), primary_key=True)
    rollout_id = Column(String(64), ForeignKey("ui_pilot_rollouts.id"), nullable=False)
    team_key = Column(String(64), index=True)
    operator = Column(String(255), nullable=False)
    action_type = Column(String(64), nullable=False)
    target_type = Column(String(64), nullable=True)
    target_id = Column(String(64), nullable=True)
    rationale = Column(Text, nullable=False)
    before_state_json = Column(SmartJSON(), default=dict)
    after_state_json = Column(SmartJSON(), default=dict)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    rollout = relationship("UIPilotRollout", back_populates="ledger_entries")

class UIPilotFinalReport(Base):
    __tablename__ = "ui_pilot_final_reports"

    id = Column(String(64), primary_key=True)
    rollout_id = Column(String(64), ForeignKey("ui_pilot_rollouts.id"), nullable=False)
    status = Column(String(32), nullable=False)
    recommendation = Column(String(32), nullable=False) # GO, GO_WITH_WARNINGS, EXTEND_PILOT, NO_GO
    readiness_score = Column(Float, default=0.0)
    executive_summary = Column(Text, nullable=True)
    metrics_json = Column(SmartJSON(), default=dict)
    risks_json = Column(SmartJSON(), default=list)
    incidents_json = Column(SmartJSON(), default=list)
    operator_notes_json = Column(SmartJSON(), default=list)
    report_path = Column(String(512), nullable=True)
    evidence_hash = Column(String(255), nullable=True)
    generated_at = Column(DateTime(timezone=True), default=utcnow)

    rollout = relationship("UIPilotRollout", back_populates="final_report")

# --- Phase 13: GA Hardening + Cross-Team Operations Models ---

class UIOperationsTeam(Base):
    """Represents a team responsible for maintaining specific UI projects."""
    __tablename__ = "ui_operations_teams"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    team_key: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    team_name: Mapped[str] = mapped_column(String(255), nullable=False)
    responsibilities_json: Mapped[list[str]] = mapped_column(SmartJSON(), default=list)
    owned_project_keys_json: Mapped[list[str]] = mapped_column(SmartJSON(), default=list)
    escalation_channels_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    oncall_policy_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE") # ACTIVE, PAUSED, ARCHIVED, DEPRECATED, BLOCKED

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class UIProjectOwnership(Base):
    """Detailed ownership registry for project governance."""
    __tablename__ = "ui_project_ownership"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    project_key: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    owner_team_key: Mapped[str] = mapped_column(String(64), nullable=False)
    technical_owner: Mapped[str] = mapped_column(String(255), nullable=False)
    business_owner: Mapped[str] = mapped_column(String(255), nullable=False)
    escalation_level: Mapped[int] = mapped_column(Integer, default=1)
    backup_owner: Mapped[str | None] = mapped_column(String(255))
    approval_policy_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class UIMaintenancePolicy(Base):
    """Project-specific maintenance windows and allowed automated actions."""
    __tablename__ = "ui_maintenance_policies"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    project_key: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    policy_name: Mapped[str] = mapped_column(String(128), nullable=False)
    maintenance_window_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict) # { "start_time": "02:00", "end_time": "05:00", "days": [0,6] }
    allowed_actions_json: Mapped[list[str]] = mapped_column(SmartJSON(), default=list)
    blocked_actions_json: Mapped[list[str]] = mapped_column(SmartJSON(), default=list)

    auto_repair_allowed: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_apply_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    approval_required: Mapped[bool] = mapped_column(Boolean, default=True)
    rollback_required: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class UIReleaseRecord(Base):
    """Audit record for a system-wide or project-specific release/patch."""
    __tablename__ = "ui_release_records"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    release_type: Mapped[str | None] = mapped_column(String(32)) # PATCH, MINOR, MAJOR, HOTFIX, ROLLBACK, POLICY_UPDATE
    project_keys_json: Mapped[list[str]] = mapped_column(SmartJSON(), default=list)

    summary: Mapped[str | None] = mapped_column(Text)
    changes_json: Mapped[list[dict[str, Any]]] = mapped_column(SmartJSON(), default=list)
    risk_summary_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    compatibility_notes: Mapped[str | None] = mapped_column(Text)
    rollback_notes: Mapped[str | None] = mapped_column(Text)
    evidence_hash: Mapped[str | None] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UICompatibilityCheck(Base):
    """Result of compatibility validation for routes and policies."""
    __tablename__ = "ui_compatibility_checks"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    project_key: Mapped[str | None] = mapped_column(String(64), index=True)
    version: Mapped[str | None] = mapped_column(String(32))
    status: Mapped[str | None] = mapped_column(String(32)) # PASSED, WARNING, FAILED

    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    breaking_changes_json: Mapped[list[str]] = mapped_column(SmartJSON(), default=list)
    deprecated_features_json: Mapped[list[str]] = mapped_column(SmartJSON(), default=list)
    migration_required: Mapped[bool] = mapped_column(Boolean, default=False)
    migration_notes: Mapped[str | None] = mapped_column(Text)
    evidence_hash: Mapped[str | None] = mapped_column(String(255))

class UISLOBreach(Base):
    """Detection and tracking of SLO violations."""
    __tablename__ = "ui_slo_breaches"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    project_key: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    slo_name: Mapped[str] = mapped_column(String(128), nullable=False)
    severity: Mapped[str | None] = mapped_column(String(32)) # WARNING, CRITICAL
    observed_value: Mapped[float | None] = mapped_column(Float)
    target_value: Mapped[float | None] = mapped_column(Float)

    breach_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    breach_resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), default="OPEN") # OPEN, ACKNOWLEDGED, MITIGATING, RESOLVED, WAIVED

    linked_incident_id: Mapped[uuid.UUID | None] = mapped_column(GUID, nullable=True)
    remediation_plan_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIEvidenceRetentionPolicy(Base):
    """Lifecycle policy for autonomous repair evidence."""
    __tablename__ = "ui_evidence_retention_policies"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    policy_name: Mapped[str] = mapped_column(String(128), nullable=False)
    retention_days: Mapped[int] = mapped_column(Integer, default=365)
    evidence_type: Mapped[str | None] = mapped_column(String(64)) # monitoring, repair, governance, chaos, pilot, release
    archive_after_days: Mapped[int] = mapped_column(Integer, default=90)
    delete_after_days: Mapped[int] = mapped_column(Integer, default=365)
    legal_hold: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

# Phase 12: General Availability + Multi-Project Rollout Models

class UIRepairProjectProfile(Base):
    """Configuration and policy for a specific project's UI repair pipeline."""
    __tablename__ = "ui_repair_project_profiles"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    project_key: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    project_name: Mapped[str] = mapped_column(String(255), nullable=False)
    environment: Mapped[str] = mapped_column(String(32), default="PRODUCTION")
    owner: Mapped[str | None] = mapped_column(String(255))

    route_scope_json: Mapped[list[str]] = mapped_column(SmartJSON(), default=list)
    critical_routes_json: Mapped[list[str]] = mapped_column(SmartJSON(), default=list)
    safety_policy_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    governance_policy_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)

    auto_repair_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_apply_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    approval_required: Mapped[bool] = mapped_column(Boolean, default=True)

    status: Mapped[str] = mapped_column(String(32), default="DRAFT") # DRAFT, PILOT, ACTIVE, PAUSED, BLOCKED, DECOMMISSIONED

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class UIRolloutWave(Base):
    """Staged deployment of projects into General Availability."""
    __tablename__ = "ui_rollout_waves"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    wave_name: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PLANNED") # PLANNED, RUNNING, COMPLETED, FAILED, PAUSED, ROLLED_BACK

    project_keys_json: Mapped[list[str]] = mapped_column(SmartJSON(), default=list)
    rollout_mode: Mapped[str] = mapped_column(String(32), default="GOVERNED_REPAIR")

    success_criteria_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    failure_criteria_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    summary_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class UIProjectHealthSnapshot(Base):
    """Point-in-time health metrics for a project."""
    __tablename__ = "ui_project_health_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    project_key: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    health_score: Mapped[float] = mapped_column(Float, default=100.0)
    monitoring_status: Mapped[str | None] = mapped_column(String(32))

    open_cases: Mapped[int] = mapped_column(Integer, default=0)
    critical_cases: Mapped[int] = mapped_column(Integer, default=0)
    governance_waiting: Mapped[int] = mapped_column(Integer, default=0)
    active_repairs: Mapped[int] = mapped_column(Integer, default=0)

    last_incident_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sla_status: Mapped[str | None] = mapped_column(String(32))
    slo_status: Mapped[str | None] = mapped_column(String(32))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIGAReadinessAssessment(Base):
    """Enterprise-wide assessment of GA readiness."""
    __tablename__ = "ui_ga_readiness_assessments"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    status: Mapped[str] = mapped_column(String(32), default="PENDING")
    readiness_score: Mapped[float] = mapped_column(Float, default=0.0)

    project_count: Mapped[int] = mapped_column(Integer, default=0)
    passed_projects: Mapped[int] = mapped_column(Integer, default=0)
    warning_projects: Mapped[int] = mapped_column(Integer, default=0)
    blocked_projects: Mapped[int] = mapped_column(Integer, default=0)

    blockers_json: Mapped[list[str]] = mapped_column(SmartJSON(), default=list)
    warnings_json: Mapped[list[str]] = mapped_column(SmartJSON(), default=list)

    recommendation: Mapped[str | None] = mapped_column(String(32)) # GA_READY, GA_WITH_WARNINGS, LIMITED_GA, EXTEND_PILOT, NO_GO
    assessed_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIEnterpriseRunbook(Base):
    """Automatically generated operating guide for enterprise deployment."""
    __tablename__ = "ui_enterprise_runbooks"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    scope: Mapped[str | None] = mapped_column(String(128))

    content: Mapped[str | None] = mapped_column(Text)
    evidence_hash: Mapped[str | None] = mapped_column(String(255))

    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

# Phase 14: Enterprise FinOps + Capacity Planning + Cost-Aware Autonomy Models

class UICostEvent(Base):
    """Granular tracking of every agent/LLM/tool call and its associated cost."""
    __tablename__ = "ui_cost_events"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    project_key: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    team_key: Mapped[str | None] = mapped_column(String(64), index=True)
    tenant_key: Mapped[str | None] = mapped_column(String(64), index=True)
    cluster_key: Mapped[str | None] = mapped_column(String(64), index=True)

    source_type: Mapped[str] = mapped_column(String(64)) # AGENT, TOOL, MONITORING, REPAIR
    source_id: Mapped[str | None] = mapped_column(String(128)) # case_id, drill_id, etc.
    operation_type: Mapped[str] = mapped_column(String(64), index=True) # MONITORING_RUN, STAGEHAND_DIAGNOSTIC, etc.

    provider: Mapped[str | None] = mapped_column(String(64)) # OPENAI, ANTHROPIC, OPENROUTER
    model: Mapped[str | None] = mapped_column(String(128))

    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    tool_calls: Mapped[int] = mapped_column(Integer, default=0)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)

    estimated_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIBudgetPolicy(Base):
    """Financial guardrails for projects and teams."""
    __tablename__ = "ui_budget_policies"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    project_key: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
    team_key: Mapped[str | None] = mapped_column(String(64), index=True)
    tenant_key: Mapped[str | None] = mapped_column(String(64), index=True)
    cluster_key: Mapped[str | None] = mapped_column(String(64), index=True)

    daily_budget_usd: Mapped[float] = mapped_column(Float, default=10.0)
    weekly_budget_usd: Mapped[float] = mapped_column(Float, default=50.0)
    monthly_budget_usd: Mapped[float] = mapped_column(Float, default=200.0)

    hard_limit_usd: Mapped[float] = mapped_column(Float, default=500.0)
    soft_limit_percent: Mapped[float] = mapped_column(Float, default=80.0)

    action_on_soft_limit: Mapped[str] = mapped_column(String(32), default="NOTIFY") # NOTIFY, LOG
    action_on_hard_limit: Mapped[str] = mapped_column(String(32), default="BLOCK") # BLOCK, NOTIFY_ONLY, GOVERNANCE_ONLY

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class UICostAnomaly(Base):
    """Detection of unexpected spikes in operational costs."""
    __tablename__ = "ui_cost_anomalies"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    project_key: Mapped[str] = mapped_column(String(64), index=True)

    anomaly_type: Mapped[str] = mapped_column(String(64)) # SPIKE, REPETITIVE_FAILURE, UNKNOWN_SOURCE
    severity: Mapped[str] = mapped_column(String(32), default="MEDIUM") # LOW, MEDIUM, HIGH, CRITICAL

    observed_cost_usd: Mapped[float] = mapped_column(Float)
    expected_cost_usd: Mapped[float] = mapped_column(Float)
    deviation_percent: Mapped[float] = mapped_column(Float)

    reason: Mapped[str | None] = mapped_column(Text)
    linked_event_ids_json: Mapped[list[str]] = mapped_column(SmartJSON(), default=list)

    status: Mapped[str] = mapped_column(String(32), default="OPEN") # OPEN, ACKNOWLEDGED, RESOLVED, WAIVED

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

class UICapacityForecast(Base):
    """Forward-looking operational and financial predictions."""
    __tablename__ = "ui_capacity_forecasts"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    project_key: Mapped[str] = mapped_column(String(64), index=True)

    forecast_window: Mapped[str] = mapped_column(String(32)) # 7D, 30D, 90D
    expected_monitoring_runs: Mapped[int] = mapped_column(Integer, default=0)
    expected_repair_attempts: Mapped[int] = mapped_column(Integer, default=0)
    expected_verifier_runs: Mapped[int] = mapped_column(Integer, default=0)
    expected_llm_calls: Mapped[int] = mapped_column(Integer, default=0)

    expected_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIFinOpsRecommendation(Base):
    """Automated suggestions for improving cost-efficiency."""
    __tablename__ = "ui_finops_recommendations"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    project_key: Mapped[str] = mapped_column(String(64), index=True)

    recommendation_type: Mapped[str] = mapped_column(String(64)) # reduce_monitoring, etc.
    priority: Mapped[str] = mapped_column(String(32), default="MEDIUM") # LOW, MEDIUM, HIGH

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    expected_savings_usd: Mapped[float] = mapped_column(Float, default=0.0)
    risk_impact: Mapped[str] = mapped_column(String(32), default="LOW") # NONE, LOW, MEDIUM, HIGH

    status: Mapped[str] = mapped_column(String(32), default="PENDING") # PENDING, APPLIED, REJECTED, IGNORED

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

# --- Phase 15: Autonomous Ecosystem Governance + Policy-as-Code (PaC) Models ---

class UIPolicyRule(Base):
    """Represents a Policy-as-Code rule that governs autonomous behavior."""
    __tablename__ = "ui_policy_rules"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    policy_key: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    scope: Mapped[str] = mapped_column(String(32), default="GLOBAL") # GLOBAL, TENANT, CLUSTER, PROJECT, TEAM, ROUTE, ACTION
    tenant_key: Mapped[str | None] = mapped_column(String(64), index=True)
    cluster_key: Mapped[str | None] = mapped_column(String(64), index=True)
    project_key: Mapped[str | None] = mapped_column(String(64), index=True)

    rule_type: Mapped[str] = mapped_column(String(64), default="AUTO_REPAIR") # AUTO_REPAIR, AUTO_APPLY, etc.
    priority: Mapped[int] = mapped_column(Integer, default=100)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    rule_definition_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    description: Mapped[str | None] = mapped_column(Text)

    created_by: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class UIPolicyEvaluation(Base):
    """Audit trail for every policy evaluation performed by the engine."""
    __tablename__ = "ui_policy_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    policy_key: Mapped[str | None] = mapped_column(String(64), index=True)
    tenant_key: Mapped[str | None] = mapped_column(String(64), index=True)
    cluster_key: Mapped[str | None] = mapped_column(String(64), index=True)
    project_key: Mapped[str] = mapped_column(String(64), index=True)

    action_type: Mapped[str] = mapped_column(String(64)) # e.g., 'APPROVE_AND_APPLY'
    target_type: Mapped[str | None] = mapped_column(String(64))
    target_id: Mapped[str | None] = mapped_column(String(64))

    decision: Mapped[str] = mapped_column(String(32)) # ALLOW, DENY, REQUIRE_APPROVAL, etc.
    reason: Mapped[str | None] = mapped_column(Text)

    matched_rules_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    input_context_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    output_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)

    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIPolicyConflict(Base):
    """Records detected conflicts between global and project-level policies."""
    __tablename__ = "ui_policy_conflicts"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    global_policy_key: Mapped[str] = mapped_column(String(64))
    project_policy_key: Mapped[str] = mapped_column(String(64))
    project_key: Mapped[str] = mapped_column(String(64), index=True)

    conflict_type: Mapped[str] = mapped_column(String(64))
    resolution: Mapped[str] = mapped_column(String(64))
    reason: Mapped[Text] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

class UIPolicyProposal(Base):
    """Lifecycle for proposing and approving new governance policies."""
    __tablename__ = "ui_policy_proposals"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    proposal_type: Mapped[str] = mapped_column(String(64)) # NEW, UPDATE, DELETE
    policy_key: Mapped[str] = mapped_column(String(64))
    scope: Mapped[str] = mapped_column(String(32))
    tenant_key: Mapped[str | None] = mapped_column(String(64), index=True)
    cluster_key: Mapped[str | None] = mapped_column(String(64), index=True)
    project_key: Mapped[str | None] = mapped_column(String(64))

    proposed_rule_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    rationale: Mapped[str] = mapped_column(Text)
    risk_level: Mapped[str] = mapped_column(String(32)) # LOW, MEDIUM, HIGH, CRITICAL

    status: Mapped[str] = mapped_column(String(32), default="DRAFT") # DRAFT, SUBMITTED, APPROVED, etc.

    proposed_by: Mapped[str] = mapped_column(String(255))
    reviewed_by: Mapped[str | None] = mapped_column(String(255))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIAutonomousOverride(Base):
    """Records manual overrides of blocked autonomous actions."""
    __tablename__ = "ui_autonomous_overrides"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    tenant_key: Mapped[str | None] = mapped_column(String(64), index=True)
    cluster_key: Mapped[str | None] = mapped_column(String(64), index=True)
    action_type: Mapped[str] = mapped_column(String(64))
    target_type: Mapped[str] = mapped_column(String(64))
    target_id: Mapped[str] = mapped_column(String(64))

    blocked_policy_key: Mapped[str] = mapped_column(String(64))
    override_reason: Mapped[str] = mapped_column(Text)
    operator: Mapped[str] = mapped_column(String(255))

    risk_level: Mapped[str] = mapped_column(String(32))
    approval_id: Mapped[str | None] = mapped_column(String(64))
    evidence_hash: Mapped[str | None] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIComplianceFinding(Base):
    """Audit of compliance violations found in the ecosystem."""
    __tablename__ = "ui_compliance_findings"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    tenant_key: Mapped[str | None] = mapped_column(String(64), index=True)
    cluster_key: Mapped[str | None] = mapped_column(String(64), index=True)
    project_key: Mapped[str] = mapped_column(String(64), index=True)
    source_type: Mapped[str] = mapped_column(String(64)) # e.g., 'PATCH', 'LOG', 'CONFIG'
    source_id: Mapped[str] = mapped_column(String(64))

    standard: Mapped[str] = mapped_column(String(64)) # INTERNAL_SECURITY, GDPR_LIKE, etc.
    severity: Mapped[str] = mapped_column(String(32)) # LOW, MEDIUM, HIGH, CRITICAL
    finding_type: Mapped[str] = mapped_column(String(64))

    description: Mapped[str] = mapped_column(Text)
    recommendation: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="OPEN") # OPEN, RESOLVED, DISMISSED

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

# --- Phase 16: Multi-Tenant Federation + Cross-Cluster Governance Models ---

class UITenantProfile(Base):
    """Phase 16: Multi-tenant organization profile."""
    __tablename__ = "ui_tenant_profiles"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    tenant_key: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    tenant_name: Mapped[str] = mapped_column(String(255), nullable=False)

    status: Mapped[str] = mapped_column(String(32), default="ACTIVE") # ACTIVE, SUSPENDED, DELETED
    governance_level: Mapped[str] = mapped_column(String(32), default="STANDARD") # STANDARD, STRICT, RELAXED

    contact_info: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    tenant_metadata: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class UIClusterProfile(Base):
    """Phase 16: Regional or environmental cluster profile."""
    __tablename__ = "ui_cluster_profiles"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    cluster_key: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    cluster_name: Mapped[str] = mapped_column(String(255), nullable=False)

    region: Mapped[str] = mapped_column(String(64), default="global")
    environment: Mapped[str] = mapped_column(String(32), default="production") # prod, staging, dev

    provider: Mapped[str] = mapped_column(String(64), default="Sovereign") # Sovereign, GKE, AWS, OnPrem
    status: Mapped[str] = mapped_column(String(32), default="HEALTHY") # HEALTHY, DEGRADED, OFFLINE

    cluster_metadata: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class UITenantProjectBinding(Base):
    """Phase 16: Mapping projects to tenants and clusters."""
    __tablename__ = "ui_tenant_project_bindings"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    tenant_key: Mapped[str] = mapped_column(String(64), ForeignKey("ui_tenant_profiles.tenant_key"), index=True)
    cluster_key: Mapped[str | None] = mapped_column(String(64), ForeignKey("ui_cluster_profiles.cluster_key"), index=True, nullable=True)
    project_key: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    binding_status: Mapped[str] = mapped_column(String(32), default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIClusterHealthSnapshot(Base):
    """Phase 16: Time-series health status of a federated cluster."""
    __tablename__ = "ui_cluster_health_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    cluster_key: Mapped[str] = mapped_column(String(64), index=True)

    health_score: Mapped[float] = mapped_column(Float, default=100.0)
    active_repairs: Mapped[int] = mapped_column(Integer, default=0)
    failed_repairs_24h: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)

    status_brief: Mapped[str] = mapped_column(String(255))
    metrics_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)

    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIFederatedEvidenceRecord(Base):
    """Phase 16: Centralized record of evidence hashes from all clusters."""
    __tablename__ = "ui_federated_evidence_records"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    tenant_key: Mapped[str] = mapped_column(String(64), index=True)
    cluster_key: Mapped[str] = mapped_column(String(64), index=True)
    project_key: Mapped[str] = mapped_column(String(64), index=True)

    source_evidence_id: Mapped[str] = mapped_column(String(64))
    evidence_type: Mapped[str] = mapped_column(String(64))
    evidence_hash: Mapped[str] = mapped_column(String(255))

    sync_status: Mapped[str] = mapped_column(String(32), default="SYNCED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIPolicyDrift(Base):
    """Phase 16: Detection of deviations between local and global policies."""
    __tablename__ = "ui_policy_drifts"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    tenant_key: Mapped[str] = mapped_column(String(64), index=True)
    cluster_key: Mapped[str | None] = mapped_column(String(64), index=True)
    project_key: Mapped[str | None] = mapped_column(String(64), index=True)

    policy_key: Mapped[str] = mapped_column(String(64), index=True)
    drift_type: Mapped[str] = mapped_column(String(64)) # RELAXED_RESTRICTION, DISABLED_GLOBAL_RULE, etc.
    drift_level: Mapped[str] = mapped_column(String(32), default="MEDIUM") # LOW, MEDIUM, HIGH, CRITICAL

    global_definition: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    local_definition: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)

    status: Mapped[str] = mapped_column(String(32), default="DETECTED") # DETECTED, ACKNOWLEDGED, RESOLVED
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

# --- Phase 17: Enterprise Resiliency Mesh + Global Load Sovereignty Models ---

class MeshNodeStatus(str, enum.Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    SATURATED = "SATURATED"
    UNREACHABLE = "UNREACHABLE"
    FAILOVER_ACTIVE = "FAILOVER_ACTIVE"
    MAINTENANCE = "MAINTENANCE"
    BLOCKED_BY_POLICY = "BLOCKED_BY_POLICY"

class FailoverTrigger(str, enum.Enum):
    HEALTH_DEGRADATION = "HEALTH_DEGRADATION"
    LATENCY_SPIKE = "LATENCY_SPIKE"
    COST_LIMIT = "COST_LIMIT"
    CAPACITY_EXHAUSTED = "CAPACITY_EXHAUSTED"
    SLO_BREACH = "SLO_BREACH"
    REGION_OUTAGE = "REGION_OUTAGE"
    CHAOS_DRILL = "CHAOS_DRILL"
    MANUAL_OPERATOR = "MANUAL_OPERATOR"

class WorkloadType(str, enum.Enum):
    MONITORING_RUN = "MONITORING_RUN"
    STAGEHAND_DIAGNOSTIC = "STAGEHAND_DIAGNOSTIC"
    OPENSWE_REPAIR = "OPENSWE_REPAIR"
    PR_AGENT_REVIEW = "PR_AGENT_REVIEW"
    VERIFIER_MESH_RUN = "VERIFIER_MESH_RUN"
    CHAOS_DRILL = "CHAOS_DRILL"
    PROOF_PACK_GENERATION = "PROOF_PACK_GENERATION"
    POSTMORTEM_GENERATION = "POSTMORTEM_GENERATION"

class UIResiliencyMeshNode(Base):
    """Phase 17: Real-time status of a mesh node (cluster)."""
    __tablename__ = "ui_resiliency_mesh_nodes"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    tenant_key: Mapped[str] = mapped_column(String(64), index=True)
    cluster_key: Mapped[str] = mapped_column(String(64), index=True, unique=True)

    region: Mapped[str] = mapped_column(String(64))
    environment: Mapped[str] = mapped_column(String(32))

    status: Mapped[str] = mapped_column(String(32), default="HEALTHY") # MeshNodeStatus
    health_score: Mapped[float] = mapped_column(Float, default=100.0)
    capacity_score: Mapped[float] = mapped_column(Float, default=100.0)
    cost_score: Mapped[float] = mapped_column(Float, default=100.0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)

    active_repairs: Mapped[int] = mapped_column(Integer, default=0)
    queue_depth: Mapped[int] = mapped_column(Integer, default=0)

    last_heartbeat_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class UIClusterFailoverEvent(Base):
    """Phase 17: Record of cluster failover operations."""
    __tablename__ = "ui_cluster_failover_events"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    source_cluster_key: Mapped[str] = mapped_column(String(64), index=True)
    target_cluster_key: Mapped[str] = mapped_column(String(64), index=True)
    tenant_key: Mapped[str] = mapped_column(String(64), index=True)

    reason: Mapped[str] = mapped_column(Text)
    trigger_type: Mapped[str] = mapped_column(String(64)) # FailoverTrigger
    severity: Mapped[str] = mapped_column(String(16), default="medium")

    decision_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    success: Mapped[bool] = mapped_column(Boolean, default=False)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    evidence_hash: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIGlobalLoadSteeringDecision(Base):
    """Phase 17: Audit trail for global workload steering decisions."""
    __tablename__ = "ui_global_load_steering_decisions"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    tenant_key: Mapped[str] = mapped_column(String(64), index=True)
    project_key: Mapped[str] = mapped_column(String(64), index=True)

    source_cluster_key: Mapped[str | None] = mapped_column(String(64))
    selected_cluster_key: Mapped[str] = mapped_column(String(64), index=True)

    workload_type: Mapped[str] = mapped_column(String(64)) # WorkloadType
    decision_reason: Mapped[str] = mapped_column(Text)

    health_score: Mapped[float] = mapped_column(Float)
    cost_score: Mapped[float] = mapped_column(Float)
    latency_score: Mapped[float] = mapped_column(Float)
    policy_score: Mapped[float] = mapped_column(Float)
    final_score: Mapped[float] = mapped_column(Float)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIMeshChaosRun(Base):
    """Phase 17: Results of cross-cluster chaos engineering drills."""
    __tablename__ = "ui_mesh_chaos_runs"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    scenario_name: Mapped[str] = mapped_column(String(255))
    target_cluster_key: Mapped[str] = mapped_column(String(64), index=True)
    target_region: Mapped[str] = mapped_column(String(64))

    chaos_type: Mapped[str] = mapped_column(String(64))
    expected_behavior: Mapped[str] = mapped_column(Text)
    detected_behavior: Mapped[str] = mapped_column(Text)

    recovery_success: Mapped[bool] = mapped_column(Boolean, default=False)
    failover_triggered: Mapped[bool] = mapped_column(Boolean, default=False)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    evidence_path: Mapped[str | None] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIGlobalSLOSnapshot(Base):
    """Phase 17: Aggregated federation-wide SLO compliance snapshot."""
    __tablename__ = "ui_global_slo_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    tenant_key: Mapped[str | None] = mapped_column(String(64), index=True) # None for Global

    federation_health_score: Mapped[float] = mapped_column(Float)
    global_mttr_s: Mapped[float] = mapped_column(Float)
    global_detection_latency_s: Mapped[float] = mapped_column(Float)

    repair_success_rate: Mapped[float] = mapped_column(Float)
    failover_success_rate: Mapped[float] = mapped_column(Float)
    policy_violation_count: Mapped[int] = mapped_column(Integer, default=0)
    evidence_sync_success_rate: Mapped[float] = mapped_column(Float, default=100.0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIAutomatedPostmortem(Base):
    """Phase 17: LLM-generated incident post-mortem analysis."""
    __tablename__ = "ui_automated_postmortems"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    incident_id: Mapped[uuid.UUID | None] = mapped_column(GUID, index=True)

    tenant_key: Mapped[str] = mapped_column(String(64), index=True)
    cluster_key: Mapped[str] = mapped_column(String(64), index=True)

    title: Mapped[str] = mapped_column(String(255))
    root_cause: Mapped[str] = mapped_column(Text)

    timeline_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    impact_summary: Mapped[str] = mapped_column(Text)

    contributing_factors_json: Mapped[list[dict[str, Any]]] = mapped_column(SmartJSON(), default=list)
    remediation_actions_json: Mapped[list[dict[str, Any]]] = mapped_column(SmartJSON(), default=list)
    prevention_actions_json: Mapped[list[dict[str, Any]]] = mapped_column(SmartJSON(), default=list)

    evidence_hash: Mapped[str | None] = mapped_column(String(255))
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class ToolType(str, enum.Enum):
    MCP_SERVER = "MCP_SERVER"
    GITHUB = "GITHUB"
    GITLAB = "GITLAB"
    BROWSER_AUTOMATION = "BROWSER_AUTOMATION"
    LLM_PROVIDER = "LLM_PROVIDER"
    NOTIFICATION_PROVIDER = "NOTIFICATION_PROVIDER"
    ISSUE_TRACKER = "ISSUE_TRACKER"
    CLOUD_API = "CLOUD_API"
    FILE_SYSTEM = "FILE_SYSTEM"
    DATABASE = "DATABASE"
    WEB_SEARCH = "WEB_SEARCH"
    CUSTOM_API = "CUSTOM_API"

class ToolDecision(str, enum.Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    REQUIRE_SANDBOX = "REQUIRE_SANDBOX"
    READ_ONLY = "READ_ONLY"
    SIMULATION_ONLY = "SIMULATION_ONLY"

class ToolViolationType(str, enum.Enum):
    SECRET_EXPOSURE = "SECRET_EXPOSURE"
    CROSS_TENANT_ACCESS = "CROSS_TENANT_ACCESS"
    POLICY_BYPASS = "POLICY_BYPASS"
    UNAPPROVED_WRITE = "UNAPPROVED_WRITE"
    UNSAFE_NETWORK_ACCESS = "UNSAFE_NETWORK_ACCESS"
    MALICIOUS_OUTPUT = "MALICIOUS_OUTPUT"
    COST_LIMIT_EXCEEDED = "COST_LIMIT_EXCEEDED"
    PROVIDER_UNHEALTHY = "PROVIDER_UNHEALTHY"
    TOOL_NOT_REGISTERED = "TOOL_NOT_REGISTERED"
    ACTION_NOT_ALLOWED = "ACTION_NOT_ALLOWED"

class ProviderStatus(str, enum.Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    RATE_LIMITED = "RATE_LIMITED"
    BLOCKED_BY_POLICY = "BLOCKED_BY_POLICY"
    UNKNOWN = "UNKNOWN"

class UIExternalTool(Base):
    """Phase 18: Registry of allowed external tools and their safety policies."""
    __tablename__ = "ui_external_tools"

    id           = Column(GUID, primary_key=True, default=uuid.uuid4)
    tool_key     = Column(String(64), unique=True, index=True)
    tool_name    = Column(String(128))
    tool_type    = Column(String(32)) # ToolType
    provider     = Column(String(128))
    description  = Column(Text)
    enabled      = Column(Boolean, default=True)
    risk_level   = Column(String(32), default="MEDIUM")

    tenant_scope_json   = Column(SmartJSON(), default=list) # List of allowed tenant_keys
    project_scope_json  = Column(SmartJSON(), default=list) # List of allowed project_keys
    allowed_actions_json = Column(SmartJSON(), default=list)
    blocked_actions_json = Column(SmartJSON(), default=list)

    requires_approval   = Column(Boolean, default=False)
    requires_sandbox    = Column(Boolean, default=False)
    cost_policy_json    = Column(SmartJSON(), default=dict)

    created_at   = Column(DateTime(timezone=True), default=datetime.now(UTC))
    updated_at   = Column(DateTime(timezone=True), onupdate=datetime.now(UTC))

class UIMCPServer(Base):
    """Phase 18: Registry and health of Model Context Protocol (MCP) servers."""
    __tablename__ = "ui_mcp_servers"

    id           = Column(GUID, primary_key=True, default=uuid.uuid4)
    server_key   = Column(String(64), unique=True, index=True)
    server_name  = Column(String(128))
    endpoint     = Column(String(512))
    transport_type = Column(String(32), default="stdio") # stdio, sse
    enabled      = Column(Boolean, default=True)

    tenant_scope_json   = Column(SmartJSON(), default=list)
    allowed_tools_json  = Column(SmartJSON(), default=list)
    blocked_tools_json  = Column(SmartJSON(), default=list)

    auth_mode    = Column(String(32), default="NONE")
    risk_level   = Column(String(32), default="MEDIUM")
    health_status = Column(String(32), default="UNKNOWN") # ProviderStatus

    last_checked_at = Column(DateTime(timezone=True))
    created_at   = Column(DateTime(timezone=True), default=datetime.now(UTC))
    updated_at   = Column(DateTime(timezone=True), onupdate=datetime.now(UTC))

class UIToolPermission(Base):
    """Phase 18: Granular permission matrix for tool-tenant-project tuples."""
    __tablename__ = "ui_tool_permissions"

    id           = Column(GUID, primary_key=True, default=uuid.uuid4)
    tool_key     = Column(String(64), index=True)
    tenant_key   = Column(String(64), index=True)
    project_key  = Column(String(64), index=True)
    action_type  = Column(String(64), index=True)

    decision     = Column(String(32)) # ToolDecision
    reason       = Column(Text)
    requires_approval = Column(Boolean, default=False)
    requires_sandbox  = Column(Boolean, default=False)

    created_at   = Column(DateTime(timezone=True), default=datetime.now(UTC))
    updated_at   = Column(DateTime(timezone=True), onupdate=datetime.now(UTC))

class UIToolCallAudit(Base):
    """Phase 18: Non-repudiable ledger of all external tool calls."""
    __tablename__ = "ui_tool_call_audits"

    id           = Column(GUID, primary_key=True, default=uuid.uuid4)
    tool_key     = Column(String(64), index=True)
    server_key   = Column(String(64), nullable=True, index=True)
    tenant_key   = Column(String(64), index=True)
    project_key  = Column(String(64), index=True)

    caller_type  = Column(String(32)) # AGENT, OPERATOR, SYSTEM
    caller_id    = Column(String(128))
    action_type  = Column(String(128))

    input_hash   = Column(String(128))
    output_hash  = Column(String(128))
    redaction_applied = Column(Boolean, default=False)

    policy_decision = Column(String(32)) # ToolDecision
    risk_level      = Column(String(32))
    cost_estimate_usd = Column(Float, default=0.0)
    latency_ms      = Column(Integer)

    status       = Column(String(32)) # SUCCESS, FAILED, BLOCKED
    error_message = Column(Text)
    evidence_hash = Column(String(128))

    created_at   = Column(DateTime(timezone=True), default=datetime.now(UTC))

class UIToolPolicyViolation(Base):
    """Phase 18: Recorded security violations and policy breaches."""
    __tablename__ = "ui_tool_policy_violations"

    id           = Column(GUID, primary_key=True, default=uuid.uuid4)
    tool_key     = Column(String(64), index=True)
    server_key   = Column(String(64), nullable=True)
    tenant_key   = Column(String(64), index=True)
    project_key  = Column(String(64), index=True)

    violation_type = Column(String(64), index=True) # ToolViolationType
    severity     = Column(String(32), default="MEDIUM")
    description  = Column(Text)
    blocked      = Column(Boolean, default=True)

    incident_id   = Column(GUID, nullable=True)
    evidence_hash = Column(String(128))

    created_at   = Column(DateTime(timezone=True), default=datetime.now(UTC))
    resolved_at  = Column(DateTime(timezone=True))

class UIProviderHealth(Base):
    """Phase 18: Operational health of third-party API providers."""
    __tablename__ = "ui_provider_health"

    id           = Column(GUID, primary_key=True, default=uuid.uuid4)
    provider     = Column(String(128), unique=True, index=True)
    status       = Column(String(32)) # ProviderStatus

    latency_ms      = Column(Integer, default=0)
    error_rate      = Column(Float, default=0.0)
    cost_spike_detected = Column(Boolean, default=False)

    last_success_at = Column(DateTime(timezone=True))
    last_failure_at = Column(DateTime(timezone=True))
    health_score    = Column(Float, default=1.0) # 0.0 to 1.0

    created_at   = Column(DateTime(timezone=True), default=datetime.now(UTC))

class UIThirdPartyRiskAssessment(Base):
    """Phase 18: Periodic risk assessment for external integrations."""
    __tablename__ = "ui_third_party_risk_assessments"

    id           = Column(GUID, primary_key=True, default=uuid.uuid4)
    provider     = Column(String(128), index=True)
    tool_key     = Column(String(64), nullable=True, index=True)

    risk_score   = Column(Float) # 0 to 100
    risk_level   = Column(String(32)) # LOW, MEDIUM, HIGH, CRITICAL
    findings_json = Column(SmartJSON(), default=list)
    recommendation = Column(Text)

    assessed_at  = Column(DateTime(timezone=True), default=datetime.now(UTC))

# --- Phase 19: Sovereign Identity Framework v2 ---

class IdentityType(str, enum.Enum):
    AGENT = "AGENT"
    WORKER = "WORKER"
    TOOL = "TOOL"
    MCP_SERVER = "MCP_SERVER"
    CLUSTER_NODE = "CLUSTER_NODE"
    OPERATOR = "OPERATOR"
    SERVICE_ACCOUNT = "SERVICE_ACCOUNT"

class IdentityStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    REVOKED = "REVOKED"
    QUARANTINED = "QUARANTINED"

class HandshakeStatus(str, enum.Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    BLOCKED_BY_POLICY = "BLOCKED_BY_POLICY"
    BLOCKED_BY_SCOPE = "BLOCKED_BY_SCOPE"
    BLOCKED_BY_STALE_TOKEN = "BLOCKED_BY_STALE_TOKEN"
    BLOCKED_BY_REPLAY_GUARD = "BLOCKED_BY_REPLAY_GUARD"

class UISovereignIdentity(Base):
    """Phase 19: Unified identity registry for all entities."""
    __tablename__ = "ui_sovereign_identities"

    id           = Column(GUID, primary_key=True, default=uuid.uuid4)
    identity_key = Column(String(128), unique=True, index=True)
    identity_type = Column(String(32)) # IdentityType
    display_name = Column(String(128))

    tenant_key   = Column(String(64), index=True)
    project_key  = Column(String(64), index=True)
    cluster_key  = Column(String(64), index=True)

    allowed_actions_json = Column(SmartJSON(), default=list)
    trust_level  = Column(String(32), default="STANDARD")
    status       = Column(String(32), default="ACTIVE") # IdentityStatus

    public_key_fingerprint = Column(String(128))

    created_at   = Column(DateTime(timezone=True), default=datetime.now(UTC))
    updated_at   = Column(DateTime(timezone=True), default=datetime.now(UTC), onupdate=datetime.now(UTC))

class UICapabilityToken(Base):
    """Phase 19: Short-lived, scoped authorization tokens."""
    __tablename__ = "ui_capability_tokens"

    id           = Column(GUID, primary_key=True, default=uuid.uuid4)
    token_id     = Column(String(128), unique=True, index=True)
    subject_identity_key = Column(String(128), index=True)

    scope_json   = Column(SmartJSON(), default=dict)
    allowed_actions_json = Column(SmartJSON(), default=list)

    expires_at   = Column(DateTime(timezone=True))
    revoked_at   = Column(DateTime(timezone=True))
    issued_by    = Column(String(128))

    evidence_hash = Column(String(128))
    created_at   = Column(DateTime(timezone=True), default=datetime.now(UTC))

class UIAgentHandshake(Base):
    """Phase 19: Records of agent-to-agent cryptographic handshakes."""
    __tablename__ = "ui_agent_handshakes"

    id           = Column(GUID, primary_key=True, default=uuid.uuid4)
    source_identity_key = Column(String(128), index=True)
    target_identity_key = Column(String(128), index=True)

    handshake_status = Column(String(32)) # HandshakeStatus
    nonce        = Column(String(64), unique=True)
    signed_context_hash = Column(String(128))

    tenant_key   = Column(String(64), index=True)
    project_key  = Column(String(64), index=True)
    cluster_key  = Column(String(64), index=True)

    action_type  = Column(String(64))
    risk_level   = Column(String(32))

    created_at   = Column(DateTime(timezone=True), default=datetime.now(UTC))

class UIIdentityAuditEvent(Base):
    """Phase 19: Audit trail for identity and trust events."""
    __tablename__ = "ui_identity_audit_events"

    id           = Column(GUID, primary_key=True, default=uuid.uuid4)
    identity_key = Column(String(128), index=True)
    event_type   = Column(String(64), index=True) # CREATED, REVOKED, HANDSHAKE_FAIL, etc.
    action_type  = Column(String(64), nullable=True)

    decision     = Column(String(32))
    reason       = Column(Text)

    tenant_key   = Column(String(64), index=True)
    project_key  = Column(String(64), index=True)
    cluster_key  = Column(String(64), index=True)

    evidence_hash = Column(String(128))
    created_at   = Column(DateTime(timezone=True), default=datetime.now(UTC))

class UITrustScore(Base):
    """Phase 19: Dynamic behavior-based trust scoring."""
    __tablename__ = "ui_trust_scores"

    id           = Column(GUID, primary_key=True, default=uuid.uuid4)
    identity_key = Column(String(128), unique=True, index=True)

    trust_score  = Column(Float, default=1.0) # 0.0 to 1.0
    success_count = Column(Integer, default=0)
    policy_violation_count = Column(Integer, default=0)
    failed_handshake_count = Column(Integer, default=0)
    stale_token_count = Column(Integer, default=0)

    last_updated_at = Column(DateTime(timezone=True), default=datetime.now(UTC))

class UICognitiveStatus(enum.Enum):
    PENDING = "PENDING"
    PASSED = "PASSED"
    WARNING = "WARNING"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"

class UICognitiveOutputType(enum.Enum):
    STAGEHAND_DIAGNOSTIC = "STAGEHAND_DIAGNOSTIC"
    OPENSWE_REPAIR_INSTRUCTION = "OPENSWE_REPAIR_INSTRUCTION"
    PR_AGENT_REVIEW = "PR_AGENT_REVIEW"
    VERIFIER_SUMMARY = "VERIFIER_SUMMARY"
    POSTMORTEM_REPORT = "POSTMORTEM_REPORT"
    POLICY_PROPOSAL = "POLICY_PROPOSAL"
    FINOPS_RECOMMENDATION = "FINOPS_RECOMMENDATION"
    RED_TEAM_SCENARIO = "RED_TEAM_SCENARIO"
    GOVERNANCE_SUMMARY = "GOVERNANCE_SUMMARY"
    RELEASE_NOTE = "RELEASE_NOTE"
    PILOT_REPORT = "PILOT_REPORT"

class UICognitiveFindingType(enum.Enum):
    UNSUPPORTED_CLAIM = "UNSUPPORTED_CLAIM"
    FABRICATED_FILE = "FABRICATED_FILE"
    FABRICATED_ENDPOINT = "FABRICATED_ENDPOINT"
    FABRICATED_TEST_RESULT = "FABRICATED_TEST_RESULT"
    FABRICATED_POLICY = "FABRICATED_POLICY"
    MISSING_EVIDENCE = "MISSING_EVIDENCE"
    WRONG_ROOT_CAUSE = "WRONG_ROOT_CAUSE"
    RISK_UNDERSTATEMENT = "RISK_UNDERSTATEMENT"
    CONTEXT_DRIFT = "CONTEXT_DRIFT"
    CONTRADICTORY_RECOMMENDATION = "CONTRADICTORY_RECOMMENDATION"
    UNSAFE_REPAIR_INSTRUCTION = "UNSAFE_REPAIR_INSTRUCTION"
    POLICY_DRIFT = "POLICY_DRIFT"

class UICognitiveDecision(enum.Enum):
    ALLOW = "ALLOW"
    ALLOW_WITH_WARNING = "ALLOW_WITH_WARNING"
    REQUIRE_MANUAL_REVIEW = "REQUIRE_MANUAL_REVIEW"
    BLOCK_ACTION = "BLOCK_ACTION"
    REQUEST_REGENERATION = "REQUEST_REGENERATION"
    REQUIRE_MORE_EVIDENCE = "REQUIRE_MORE_EVIDENCE"

class UICognitiveIntegrityCheck(Base):
    """Phase 20: Zero-trust verification for LLM/Agent outputs."""
    __tablename__ = "ui_cognitive_integrity_checks"

    id           = Column(GUID, primary_key=True, default=uuid.uuid4)
    source_type  = Column(String(64), index=True) # e.g., REPAIR_CASE, INCIDENT
    source_id    = Column(String(128), index=True)
    agent_name   = Column(String(64), index=True)
    output_type  = Column(SAEnum(UICognitiveOutputType), index=True)

    status       = Column(SAEnum(UICognitiveStatus), default=UICognitiveStatus.PENDING)

    integrity_score          = Column(Float, default=0.0)
    hallucination_score      = Column(Float, default=0.0) # Lower is better in finding, higher is better in integrity
    evidence_grounding_score = Column(Float, default=0.0)
    semantic_drift_score     = Column(Float, default=0.0)
    claim_verification_score = Column(Float, default=0.0)

    decision     = Column(SAEnum(UICognitiveDecision), nullable=True)
    reason       = Column(Text, nullable=True)

    created_at   = Column(DateTime(timezone=True), default=datetime.now(UTC))

class UILLMClaim(Base):
    """Phase 20: Individual claims extracted from LLM output."""
    __tablename__ = "ui_llm_claims"

    id           = Column(GUID, primary_key=True, default=uuid.uuid4)
    check_id     = Column(GUID, ForeignKey("ui_cognitive_integrity_checks.id"), index=True)

    claim_text   = Column(Text)
    claim_type   = Column(String(64)) # file, endpoint, test_result, root_cause, etc.

    verification_status = Column(String(32)) # VERIFIED, UNSUPPORTED, CONTRADICTED
    evidence_refs_json  = Column(SmartJSON(), nullable=True)

    confidence   = Column(Float, default=0.0)
    failure_reason = Column(Text, nullable=True)

    created_at   = Column(DateTime(timezone=True), default=datetime.now(UTC))

class UIHallucinationFinding(Base):
    """Phase 20: Detected hallucinations (fabricated references)."""
    __tablename__ = "ui_hallucination_findings"

    id           = Column(GUID, primary_key=True, default=uuid.uuid4)
    check_id     = Column(GUID, ForeignKey("ui_cognitive_integrity_checks.id"), index=True)

    finding_type = Column(SAEnum(UICognitiveFindingType))
    severity     = Column(String(32)) # LOW, MEDIUM, HIGH, CRITICAL
    description  = Column(Text)

    unsupported_reference = Column(String(256), nullable=True) # The fabricated file/id
    suggested_action      = Column(String(128), nullable=True)

    blocked      = Column(Boolean, default=False)
    created_at   = Column(DateTime(timezone=True), default=datetime.now(UTC))

class UISemanticDriftEvent(Base):
    """Phase 20: Records of context deviation in agent workflows."""
    __tablename__ = "ui_semantic_drift_events"

    id           = Column(GUID, primary_key=True, default=uuid.uuid4)
    source_type  = Column(String(64), index=True)
    source_id    = Column(String(128), index=True)

    expected_context_hash = Column(String(128))
    actual_context_hash   = Column(String(128))

    drift_type   = Column(String(64)) # TENANT_DRIFT, ROUTE_DRIFT, etc.
    drift_score  = Column(Float)

    severity     = Column(String(32)) # LOW, MEDIUM, HIGH, CRITICAL
    description  = Column(Text)

    created_at   = Column(DateTime(timezone=True), default=datetime.now(UTC))

class UICognitivePolicyDecision(Base):
    """Phase 20: Governance decision for cognitive checks."""
    __tablename__ = "ui_cognitive_policy_decisions"

    id           = Column(GUID, primary_key=True, default=uuid.uuid4)
    check_id     = Column(GUID, ForeignKey("ui_cognitive_integrity_checks.id"), index=True)

    action_type  = Column(String(64))
    decision     = Column(SAEnum(UICognitiveDecision))
    reason       = Column(Text)

    requires_manual_review = Column(Boolean, default=False)
    blocked_action         = Column(String(128), nullable=True)

    evidence_hash = Column(String(128))
    created_at   = Column(DateTime(timezone=True), default=datetime.now(UTC))

# --- Phase 21: Autonomous Security Posture Management + Continuous Compliance Certification ---

class UIPostureLevel(str, enum.Enum):
    SECURE = "SECURE"
    RELIABLE = "RELIABLE"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"

class UIControlStatus(str, enum.Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    WARNING = "WARNING"
    DISABLED = "DISABLED"
    NOT_APPLICABLE = "NOT_APPLICABLE"

class UISecurityPostureScore(Base):
    """Phase 21: Historical tracking of the platform's security score."""
    __tablename__ = "ui_security_posture_scores"
    __table_args__ = {"extend_existing": True}

    id           = Column(GUID, primary_key=True, default=uuid.uuid4)
    overall_score = Column(Float, default=0.0)

    # Domain specific scores
    identity_score    = Column(Float, default=0.0)
    policy_score      = Column(Float, default=0.0)
    isolation_score   = Column(Float, default=0.0)
    governance_score  = Column(Float, default=0.0)
    evidence_score    = Column(Float, default=0.0)

    posture_level     = Column(SAEnum(UIPostureLevel), default=UIPostureLevel.UNKNOWN)

    tenant_key   = Column(String(64), nullable=True) # Global if null
    created_at   = Column(DateTime(timezone=True), default=datetime.now(UTC))

class UIComplianceControl(Base):
    """Phase 21: Mandatory security controls definition matrix."""
    __tablename__ = "ui_compliance_controls"
    __table_args__ = {"extend_existing": True}

    id           = Column(GUID, primary_key=True, default=uuid.uuid4)
    control_key  = Column(String(64), unique=True)
    domain       = Column(String(64)) # IDENTITY, POLICY, ISOLATION, etc.
    title        = Column(String(128))
    description  = Column(Text)

    severity     = Column(String(32)) # LOW, MEDIUM, HIGH, CRITICAL
    is_mandatory = Column(Boolean, default=True)

    created_at   = Column(DateTime(timezone=True), default=datetime.now(UTC))

class UISecurityPostureFinding(Base):
    """Phase 21: Results of specific compliance control checks."""
    __tablename__ = "ui_security_posture_findings"
    __table_args__ = {"extend_existing": True}

    id           = Column(GUID, primary_key=True, default=uuid.uuid4)
    control_key  = Column(String(64))
    status       = Column(SAEnum(UIControlStatus))

    evidence_hash = Column(String(128))
    rationale     = Column(Text)

    tenant_key   = Column(String(64), nullable=True)
    cluster_key  = Column(String(64), nullable=True)

    last_check_at = Column(DateTime(timezone=True), default=datetime.now(UTC))
    created_at    = Column(DateTime(timezone=True), default=datetime.now(UTC))

class UISecurityCertification(Base):
    """Phase 21: Non-repudiable compliance certification records."""
    __tablename__ = "ui_security_certifications"
    __table_args__ = {"extend_existing": True}

    id           = Column(GUID, primary_key=True, default=uuid.uuid4)
    cert_id      = Column(String(128), unique=True, index=True) # Format: CERT-YYYYMMDD-XXXX

    overall_score = Column(Float)
    compliance_score = Column(Float)

    posture_level = Column(SAEnum(UIPostureLevel))

    summary_json = Column(SmartJSON(), default=dict) # Aggregated scores/findings
    findings_json = Column(SmartJSON(), default=list) # Snapshot of failed controls

    certified_by = Column(String(128)) # Agent or Operator name
    evidence_ledger_hash = Column(String(128))

    tenant_key   = Column(String(64), nullable=True)
    created_at   = Column(DateTime(timezone=True), default=datetime.now(UTC))

# --- Phase 22: Autonomous Remediation of Security Findings + Compliance Auto-Fix ---

class RemediationStatus(str, enum.Enum):
    PLANNED = "PLANNED"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    AUTO_FIX_RUNNING = "AUTO_FIX_RUNNING"
    PATCH_GENERATED = "PATCH_GENERATED"
    PR_OPENED = "PR_OPENED"
    VERIFIER_RUNNING = "VERIFIER_RUNNING"
    GOVERNANCE_REQUESTED = "GOVERNANCE_REQUESTED"
    FIX_APPLIED = "FIX_APPLIED"
    RESCAN_REQUIRED = "RESCAN_REQUIRED"
    FIX_VERIFIED = "FIX_VERIFIED"
    FAILED = "FAILED"
    MANUAL_REQUIRED = "MANUAL_REQUIRED"
    BLOCKED_BY_POLICY = "BLOCKED_BY_POLICY"

class RemediationType(str, enum.Enum):
    POLICY_TIGHTENING = "POLICY_TIGHTENING"
    CONFIG_HARDENING = "CONFIG_HARDENING"
    EVIDENCE_CHAIN_REPAIR = "EVIDENCE_CHAIN_REPAIR"
    IDENTITY_TRUST_REPAIR = "IDENTITY_TRUST_REPAIR"
    TOOL_GOVERNANCE_REPAIR = "TOOL_GOVERNANCE_REPAIR"
    TENANT_ISOLATION_REPAIR = "TENANT_ISOLATION_REPAIR"
    COMPLIANCE_METADATA_FIX = "COMPLIANCE_METADATA_FIX"
    DASHBOARD_VISIBILITY_FIX = "DASHBOARD_VISIBILITY_FIX"
    MANUAL_SECURITY_REVIEW = "MANUAL_SECURITY_REVIEW"

class UISecurityRemediationPlan(Base):
    """Phase 22: Strategy for fixing a detected security finding."""
    __tablename__ = "ui_security_remediation_plans"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    finding_id: Mapped[uuid.UUID] = mapped_column(GUID, index=True)
    finding_type: Mapped[str] = mapped_column(String(64))
    severity: Mapped[str] = mapped_column(String(32))
    risk_level: Mapped[str] = mapped_column(String(32))

    remediation_type: Mapped[RemediationType] = mapped_column(SAEnum(RemediationType))
    recommended_action: Mapped[str] = mapped_column(Text)

    affected_module: Mapped[str | None] = mapped_column(String(256))
    affected_policy: Mapped[str | None] = mapped_column(String(256))
    affected_route: Mapped[str | None] = mapped_column(String(256))

    requires_approval: Mapped[bool] = mapped_column(Boolean, default=True)
    requires_patch: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_operator: Mapped[bool] = mapped_column(Boolean, default=True)

    status: Mapped[RemediationStatus] = mapped_column(SAEnum(RemediationStatus), default=RemediationStatus.PLANNED)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class UISecurityAutoFixAttempt(Base):
    """Phase 22: Execution record of an autonomous fix."""
    __tablename__ = "ui_security_autofix_attempts"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    remediation_plan_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("ui_security_remediation_plans.id"), index=True)
    finding_id: Mapped[uuid.UUID] = mapped_column(GUID, index=True)

    status: Mapped[RemediationStatus] = mapped_column(SAEnum(RemediationStatus), default=RemediationStatus.AUTO_FIX_RUNNING)
    fix_strategy: Mapped[str] = mapped_column(String(128))

    patch_path: Mapped[str | None] = mapped_column(String(512))
    pr_url: Mapped[str | None] = mapped_column(String(512))

    verifier_status: Mapped[str | None] = mapped_column(String(32))
    governance_status: Mapped[str | None] = mapped_column(String(32))

    posture_before_score: Mapped[float] = mapped_column(Float, default=0.0)
    posture_after_score: Mapped[float | None] = mapped_column(Float)

    error_message: Mapped[str | None] = mapped_column(Text)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIComplianceFixResult(Base):
    """Phase 22: Impact analysis of a compliance fix."""
    __tablename__ = "ui_compliance_fix_results"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    finding_id: Mapped[uuid.UUID] = mapped_column(GUID, index=True)
    remediation_plan_id: Mapped[uuid.UUID] = mapped_column(GUID, index=True)

    certification_before_id: Mapped[uuid.UUID] = mapped_column(GUID, nullable=True)
    certification_after_id: Mapped[uuid.UUID] = mapped_column(GUID, nullable=True)

    compliance_status_before: Mapped[str] = mapped_column(String(32))
    compliance_status_after: Mapped[str] = mapped_column(String(32))

    fixed: Mapped[bool] = mapped_column(Boolean, default=False)
    residual_risk: Mapped[str | None] = mapped_column(Text)
    evidence_hash: Mapped[str | None] = mapped_column(String(128))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UISecurityRemediationEvent(Base):
    """Phase 22: Audit log for remediation events."""
    __tablename__ = "ui_security_remediation_events"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    finding_id: Mapped[uuid.UUID] = mapped_column(GUID, index=True)
    plan_id: Mapped[uuid.UUID] = mapped_column(GUID, index=True)
    attempt_id: Mapped[uuid.UUID | None] = mapped_column(GUID, index=True)

    event_type: Mapped[str] = mapped_column(String(64))
    message: Mapped[str] = mapped_column(Text)
    payload_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    evidence_hash: Mapped[str | None] = mapped_column(String(128))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class AssetType(str, enum.Enum):
    TENANT = "TENANT"
    PROJECT = "PROJECT"
    CLUSTER = "CLUSTER"
    IDENTITY = "IDENTITY"
    CAPABILITY_TOKEN = "CAPABILITY_TOKEN"
    MCP_SERVER = "MCP_SERVER"
    EXTERNAL_TOOL = "EXTERNAL_TOOL"
    POLICY_RULE = "POLICY_RULE"
    GOVERNANCE_APPROVAL = "GOVERNANCE_APPROVAL"
    EVIDENCE_RECORD = "EVIDENCE_RECORD"
    REPAIR_CASE = "REPAIR_CASE"
    REPAIR_ATTEMPT = "REPAIR_ATTEMPT"
    MESH_NODE = "MESH_NODE"
    PROVIDER = "PROVIDER"
    DASHBOARD_ROUTE = "DASHBOARD_ROUTE"
    API_ENDPOINT = "API_ENDPOINT"

class AttackPathType(str, enum.Enum):
    TENANT_ISOLATION_BYPASS = "TENANT_ISOLATION_BYPASS"
    POLICY_BYPASS = "POLICY_BYPASS"
    IDENTITY_IMPERSONATION = "IDENTITY_IMPERSONATION"
    TOOL_ABUSE = "TOOL_ABUSE"
    SECRET_EXFILTRATION = "SECRET_EXFILTRATION"
    EVIDENCE_TAMPERING = "EVIDENCE_TAMPERING"
    GOVERNANCE_BYPASS = "GOVERNANCE_BYPASS"
    AUTO_APPLY_ABUSE = "AUTO_APPLY_ABUSE"
    MCP_WRITE_ABUSE = "MCP_WRITE_ABUSE"
    MESH_FAILOVER_ABUSE = "MESH_FAILOVER_ABUSE"
    COGNITIVE_HALLUCINATION_EXPLOIT = "COGNITIVE_HALLUCINATION_EXPLOIT"
    COST_EXHAUSTION_ATTACK = "COST_EXHAUSTION_ATTACK"

class UIAttackSurfaceAsset(Base):
    """Phase 23: Asset inventory for threat modeling."""
    __tablename__ = "ui_attack_surface_assets"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    asset_key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    asset_type: Mapped[str] = mapped_column(String(64)) # From AssetType enum

    project_key: Mapped[str | None] = mapped_column(String(64), index=True)
    tenant_key: Mapped[str | None] = mapped_column(String(64), index=True)
    cluster_key: Mapped[str | None] = mapped_column(String(64), index=True)

    exposure_level: Mapped[str] = mapped_column(String(32)) # LOW, MEDIUM, HIGH, CRITICAL
    criticality: Mapped[str] = mapped_column(String(32)) # LOW, MEDIUM, HIGH, CRITICAL
    owner_team: Mapped[str | None] = mapped_column(String(128))

    metadata_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class UIThreatModel(Base):
    """Phase 23: High-level threat model analysis."""
    __tablename__ = "ui_threat_models"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    model_name: Mapped[str] = mapped_column(String(256))
    scope: Mapped[str] = mapped_column(String(64)) # SYSTEM, TENANT, PROJECT

    tenant_key: Mapped[str | None] = mapped_column(String(64), index=True)
    project_key: Mapped[str | None] = mapped_column(String(64), index=True)
    cluster_key: Mapped[str | None] = mapped_column(String(64), index=True)

    status: Mapped[str] = mapped_column(String(32)) # GENERATING, ACTIVE, ARCHIVED
    generated_by: Mapped[str] = mapped_column(String(128))

    summary_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    evidence_hash: Mapped[str | None] = mapped_column(String(128))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class UIAttackPath(Base):
    """Phase 23: Potential attack paths identified in the threat model."""
    __tablename__ = "ui_attack_paths"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    threat_model_id: Mapped[uuid.UUID] = mapped_column(GUID, index=True)

    path_name: Mapped[str] = mapped_column(String(256))
    path_type: Mapped[str] = mapped_column(String(64)) # From AttackPathType enum

    source_asset_key: Mapped[str] = mapped_column(String(128))
    target_asset_key: Mapped[str] = mapped_column(String(128))

    attack_steps_json: Mapped[list[dict[str, Any]]] = mapped_column(SmartJSON(), default=list)
    required_conditions_json: Mapped[list[str]] = mapped_column(SmartJSON(), default=list)

    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    severity: Mapped[str] = mapped_column(String(32)) # LOW, MEDIUM, HIGH, CRITICAL
    feasibility: Mapped[float] = mapped_column(Float, default=0.0) # 0.0 to 1.0
    impact: Mapped[float] = mapped_column(Float, default=0.0) # 0.0 to 1.0

    mitigation_status: Mapped[str] = mapped_column(String(32), default="UNMITIGATED") # UNMITIGATED, MITIGATED, PARTIAL

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIAttackSimulationRun(Base):
    """Phase 23: Results of a controlled attack simulation."""
    __tablename__ = "ui_attack_simulation_runs"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    attack_path_id: Mapped[uuid.UUID] = mapped_column(GUID, index=True)

    status: Mapped[str] = mapped_column(String(32)) # RUNNING, COMPLETED, FAILED
    simulation_mode: Mapped[str] = mapped_column(String(32)) # DRY_RUN, SHADOW, ACTIVE_TEST

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    detected_controls_json: Mapped[list[str]] = mapped_column(SmartJSON(), default=list)
    bypassed_controls_json: Mapped[list[str]] = mapped_column(SmartJSON(), default=list)
    blocked_by_json: Mapped[dict[str, Any] | None] = mapped_column(SmartJSON())

    result_summary_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    evidence_hash: Mapped[str | None] = mapped_column(String(128))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIThreatMitigation(Base):
    """Phase 23: Recommended and applied mitigations for threat paths."""
    __tablename__ = "ui_threat_mitigations"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    attack_path_id: Mapped[uuid.UUID] = mapped_column(GUID, index=True)

    mitigation_type: Mapped[str] = mapped_column(String(64))
    recommendation: Mapped[str] = mapped_column(Text)

    related_policy_key: Mapped[str | None] = mapped_column(String(128))
    related_control_id: Mapped[str | None] = mapped_column(String(128))
    remediation_plan_id: Mapped[uuid.UUID | None] = mapped_column(GUID, index=True)

    status: Mapped[str] = mapped_column(String(32)) # PENDING, LINKED, APPLIED

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

# --- Phase 24: Autonomous Red Teaming + Adversarial Drift Detection ---

class UIRedTeamScenario(Base):
    """Phase 24: Pre-defined or dynamically generated adversarial attack scenarios."""
    __tablename__ = "ui_red_team_scenarios"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    scenario_key: Mapped[str] = mapped_column(String(64), unique=True)
    scenario_name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)

    source_attack_path_id: Mapped[uuid.UUID | None] = mapped_column(GUID, ForeignKey("ui_attack_simulation_runs.id"))
    scenario_type: Mapped[RedTeamScenarioType] = mapped_column(SAEnum(RedTeamScenarioType))
    target_domain: Mapped[RedTeamTargetDomain] = mapped_column(SAEnum(RedTeamTargetDomain))
    target_asset_key: Mapped[str | None] = mapped_column(String(128))

    tenant_key: Mapped[str | None] = mapped_column(String(128))
    project_key: Mapped[str | None] = mapped_column(String(128))
    cluster_key: Mapped[str | None] = mapped_column(String(128))

    risk_level: Mapped[str] = mapped_column(String(32)) # LOW, MEDIUM, HIGH, CRITICAL
    safety_mode: Mapped[RedTeamSafetyMode] = mapped_column(SAEnum(RedTeamSafetyMode), default=RedTeamSafetyMode.SIMULATION_ONLY)

    expected_control: Mapped[str | None] = mapped_column(String(128))
    expected_block_reason: Mapped[str | None] = mapped_column(String(255))

    payload_template_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)

    enabled: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Legacy Compatibility (Phase 10)
    risk_type: Mapped[str | None] = mapped_column(String(64))
    expected_detection: Mapped[str | None] = mapped_column(String(64))
    expected_severity: Mapped[str | None] = mapped_column(String(32))
    expected_policy_decision: Mapped[str | None] = mapped_column(String(64))
    is_destructive: Mapped[bool] = mapped_column(Boolean, default=False)

class UIRedTeamRun(Base):
    """Phase 24: Execution record of an autonomous Red Team scenario."""
    __tablename__ = "ui_red_team_runs"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    scenario_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("ui_red_team_scenarios.id"))

    status: Mapped[RedTeamRunStatus] = mapped_column(SAEnum(RedTeamRunStatus), default=RedTeamRunStatus.PENDING)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    safety_mode: Mapped[RedTeamSafetyMode] = mapped_column(SAEnum(RedTeamSafetyMode))

    detected_by_control: Mapped[str | None] = mapped_column(String(128))
    blocked_by_control: Mapped[str | None] = mapped_column(String(128))

    bypassed_controls_json: Mapped[list[str]] = mapped_column(SmartJSON(), default=list)
    triggered_controls_json: Mapped[list[str]] = mapped_column(SmartJSON(), default=list)
    result_summary_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)

    evidence_hash: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    # Legacy Compatibility (Phase 10)
    actual_detection: Mapped[str | None] = mapped_column(String(64))
    actual_severity: Mapped[str | None] = mapped_column(String(32))
    actual_decision: Mapped[str | None] = mapped_column(String(64))

class UIAdversarialProbe(Base):
    """Phase 24: Individual probe within a Red Team run."""
    __tablename__ = "ui_adversarial_probes"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("ui_red_team_runs.id"))

    probe_type: Mapped[str] = mapped_column(String(64))
    target_domain: Mapped[RedTeamTargetDomain] = mapped_column(SAEnum(RedTeamTargetDomain))

    input_payload_hash: Mapped[str | None] = mapped_column(String(128))
    expected_decision: Mapped[str] = mapped_column(String(32)) # ALLOW, DENY, APPROVE
    actual_decision: Mapped[str] = mapped_column(String(32))

    passed: Mapped[bool] = mapped_column(default=False)
    failure_reason: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIAdversarialDriftEvent(Base):
    """Phase 24: Records deviations in system security behavior during adversarial pressure."""
    __tablename__ = "ui_adversarial_drift_events"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID | None] = mapped_column(GUID, ForeignKey("ui_red_team_runs.id"))

    domain: Mapped[RedTeamTargetDomain] = mapped_column(SAEnum(RedTeamTargetDomain))
    drift_type: Mapped[AdversarialDriftType] = mapped_column(SAEnum(AdversarialDriftType))

    baseline_hash: Mapped[str | None] = mapped_column(String(128))
    observed_behavior_hash: Mapped[str | None] = mapped_column(String(128))

    drift_score: Mapped[float] = mapped_column(Float)
    severity: Mapped[str] = mapped_column(String(32)) # LOW, MEDIUM, HIGH, CRITICAL
    description: Mapped[str] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIRedTeamFinding(Base):
    """Phase 24: Security findings generated from Red Team operations."""
    __tablename__ = "ui_red_team_findings"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("ui_red_team_runs.id"))
    scenario_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("ui_red_team_scenarios.id"))

    finding_type: Mapped[str] = mapped_column(String(64))
    severity: Mapped[str] = mapped_column(String(32))
    description: Mapped[str] = mapped_column(Text)

    affected_control: Mapped[str | None] = mapped_column(String(128))
    affected_domain: Mapped[RedTeamTargetDomain] = mapped_column(SAEnum(RedTeamTargetDomain))

    feasible: Mapped[bool] = mapped_column(default=False)
    remediation_plan_id: Mapped[uuid.UUID | None] = mapped_column(GUID)
    incident_id: Mapped[uuid.UUID | None] = mapped_column(GUID)

    evidence_hash: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

class UIRedTeamReport(Base):
    """Phase 24: Executive summary report for Red Team operations."""
    __tablename__ = "ui_red_team_reports"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    report_name: Mapped[str] = mapped_column(String(255))

    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    total_scenarios: Mapped[int] = mapped_column(Integer, default=0)
    passed_scenarios: Mapped[int] = mapped_column(Integer, default=0)
    failed_scenarios: Mapped[int] = mapped_column(Integer, default=0)

    critical_findings: Mapped[int] = mapped_column(Integer, default=0)
    high_findings: Mapped[int] = mapped_column(Integer, default=0)
    drift_events: Mapped[int] = mapped_column(Integer, default=0)

    executive_summary: Mapped[str] = mapped_column(Text)
    report_path: Mapped[str | None] = mapped_column(String(512))
    evidence_hash: Mapped[str | None] = mapped_column(String(128))

    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class UIGuardrailTuningProposal(Base):
    """Phase 25: Proposal for tuning a security guardrail."""
    __tablename__ = "ui_guardrail_tuning_proposals"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    proposal_key: Mapped[str] = mapped_column(String(64), unique=True)

    source_type: Mapped[str] = mapped_column(String(64)) # RED_TEAM, POSTURE, DRIFT, COMPLIANCE
    source_id: Mapped[uuid.UUID | None] = mapped_column(GUID)

    affected_guardrail: Mapped[str] = mapped_column(String(128))
    affected_policy_key: Mapped[str] = mapped_column(String(128))

    current_config_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    proposed_config_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)

    reason: Mapped[str] = mapped_column(Text)
    expected_security_gain: Mapped[float] = mapped_column(Float, default=0.0)
    expected_false_positive_impact: Mapped[float] = mapped_column(Float, default=0.0)
    expected_false_negative_impact: Mapped[float] = mapped_column(Float, default=0.0)

    risk_level: Mapped[UIRepairSeverity] = mapped_column(SAEnum(UIRepairSeverity))
    status: Mapped[GuardrailTuningStatus] = mapped_column(SAEnum(GuardrailTuningStatus), default=GuardrailTuningStatus.DRAFT)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class UIDefensivePattern(Base):
    """Phase 25: Reusable defensive pattern synthesized from findings."""
    __tablename__ = "ui_defensive_patterns"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    pattern_key: Mapped[str] = mapped_column(String(64), unique=True)
    source_finding_id: Mapped[uuid.UUID | None] = mapped_column(GUID)

    pattern_type: Mapped[str] = mapped_column(String(64)) # DETECTION, DENY, APPROVAL, SANDBOX, MONITORING, COGNITIVE, ESCALATION
    affected_domain: Mapped[GuardrailDomain] = mapped_column(SAEnum(GuardrailDomain))

    description: Mapped[str] = mapped_column(Text)
    detection_rule_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    mitigation_rule_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)

    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(32), default="DRAFT") # DRAFT, ACTIVE, DEPRECATED

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class UIPolicyRegressionRun(Base):
    """Phase 25: Verification run to check if a proposal causes regressions."""
    __tablename__ = "ui_policy_regression_runs"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    proposal_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("ui_guardrail_tuning_proposals.id"))

    status: Mapped[str] = mapped_column(String(32)) # RUNNING, PASSED, FAILED
    tested_events_count: Mapped[int] = mapped_column(Integer, default=0)
    allowed_count: Mapped[int] = mapped_column(Integer, default=0)
    denied_count: Mapped[int] = mapped_column(Integer, default=0)
    false_allow_count: Mapped[int] = mapped_column(Integer, default=0)
    false_block_count: Mapped[int] = mapped_column(Integer, default=0)

    regression_score: Mapped[float] = mapped_column(Float, default=1.0)
    result_summary_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIGuardrailCanaryRun(Base):
    """Phase 25: Real-world canary deployment of a tuning proposal."""
    __tablename__ = "ui_guardrail_canary_runs"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    proposal_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("ui_guardrail_tuning_proposals.id"))

    status: Mapped[str] = mapped_column(String(32)) # RUNNING, PASSED, FAILED
    canary_scope_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    observed_events: Mapped[int] = mapped_column(Integer, default=0)
    blocked_events: Mapped[int] = mapped_column(Integer, default=0)
    unexpected_allows: Mapped[int] = mapped_column(Integer, default=0)
    unexpected_blocks: Mapped[int] = mapped_column(Integer, default=0)

    rollback_required: Mapped[bool] = mapped_column(Boolean, default=False)
    result_summary_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIDefenseOptimizationReport(Base):
    """Phase 25: Executive report on defense optimization performance."""
    __tablename__ = "ui_defense_optimization_reports"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    report_name: Mapped[str] = mapped_column(String(255))

    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    total_proposals: Mapped[int] = mapped_column(Integer, default=0)
    approved_proposals: Mapped[int] = mapped_column(Integer, default=0)
    rejected_proposals: Mapped[int] = mapped_column(Integer, default=0)

    security_score_before: Mapped[float] = mapped_column(Float, default=0.0)
    security_score_after: Mapped[float] = mapped_column(Float, default=0.0)

    false_allow_delta: Mapped[int] = mapped_column(Integer, default=0)
    false_block_delta: Mapped[int] = mapped_column(Integer, default=0)

    executive_summary: Mapped[str] = mapped_column(Text)
    evidence_hash: Mapped[str | None] = mapped_column(String(128))

    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class UIIncidentWarRoom(Base):
    """Phase 26: Central crisis management for critical incidents."""
    __tablename__ = "ui_incident_war_rooms"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    incident_key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))

    severity: Mapped[IncidentSeverity] = mapped_column(SAEnum(IncidentSeverity), index=True)
    status: Mapped[WarRoomStatus] = mapped_column(SAEnum(WarRoomStatus), default=WarRoomStatus.OPEN, index=True)

    source_type: Mapped[IncidentSource] = mapped_column(SAEnum(IncidentSource))
    source_id: Mapped[uuid.UUID | None] = mapped_column(GUID)

    tenant_key: Mapped[str | None] = mapped_column(String(64), index=True)
    project_key: Mapped[str | None] = mapped_column(String(64), index=True)
    cluster_key: Mapped[str | None] = mapped_column(String(64), index=True)

    assigned_commander: Mapped[str | None] = mapped_column(String(128))
    owner_team: Mapped[str | None] = mapped_column(String(128))

    blast_radius_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    business_impact_score: Mapped[float] = mapped_column(Float, default=0.0)
    executive_risk_score: Mapped[float] = mapped_column(Float, default=0.0)

    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    evidence_hash: Mapped[str | None] = mapped_column(String(128))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIIncidentTimelineEvent(Base):
    """Phase 26: Event timeline for an incident."""
    __tablename__ = "ui_incident_timeline_events"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    war_room_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("ui_incident_war_rooms.id"))

    event_type: Mapped[str] = mapped_column(String(64))
    actor: Mapped[str] = mapped_column(String(128))
    message: Mapped[str] = mapped_column(Text)

    source_ref: Mapped[str | None] = mapped_column(String(255))
    payload_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    evidence_hash: Mapped[str | None] = mapped_column(String(128))

class UIExecutiveRiskSnapshot(Base):
    """Phase 26: Periodic snapshot of global executive risk."""
    __tablename__ = "ui_executive_risk_snapshots"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    snapshot_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    global_risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    active_p0_count: Mapped[int] = mapped_column(Integer, default=0)
    active_p1_count: Mapped[int] = mapped_column(Integer, default=0)

    affected_tenants: Mapped[int] = mapped_column(Integer, default=0)
    affected_clusters: Mapped[int] = mapped_column(Integer, default=0)

    open_remediations: Mapped[int] = mapped_column(Integer, default=0)
    governance_waiting: Mapped[int] = mapped_column(Integer, default=0)

    executive_summary: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIIncidentActionItem(Base):
    """Phase 26: Individual action items for incident response."""
    __tablename__ = "ui_incident_action_items"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    war_room_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("ui_incident_war_rooms.id"))

    action_type: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(255))
    owner: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), default="PENDING") # PENDING, IN_PROGRESS, COMPLETED, CANCELLED

    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    linked_remediation_id: Mapped[uuid.UUID | None] = mapped_column(GUID)
    linked_postmortem_id: Mapped[uuid.UUID | None] = mapped_column(GUID)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class UIExecutiveRiskReport(Base):
    """Phase 26: Formal executive risk report."""
    __tablename__ = "ui_executive_risk_reports"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    report_name: Mapped[str] = mapped_column(String(255))

    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    total_incidents: Mapped[int] = mapped_column(Integer, default=0)
    p0_count: Mapped[int] = mapped_column(Integer, default=0)
    p1_count: Mapped[int] = mapped_column(Integer, default=0)
    mttr_s: Mapped[float] = mapped_column(Float, default=0.0) # Mean Time To Resolve in seconds

    unresolved_risks_json: Mapped[list[dict[str, Any]]] = mapped_column(SmartJSON(), default=list)
    top_risk_domains_json: Mapped[list[str]] = mapped_column(SmartJSON(), default=list)

    recommendation: Mapped[str] = mapped_column(Text)
    report_path: Mapped[str | None] = mapped_column(String(512))
    evidence_hash: Mapped[str | None] = mapped_column(String(128))

    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AutoPatchExecutionStatus(str, enum.Enum):
    PLANNED = "PLANNED"
    PREFLIGHT_RUNNING = "PREFLIGHT_RUNNING"
    PREFLIGHT_BLOCKED = "PREFLIGHT_BLOCKED"
    PATCH_PLANNING = "PATCH_PLANNING"
    PATCH_GENERATING = "PATCH_GENERATING"
    PATCH_GENERATED = "PATCH_GENERATED"
    PR_OPENED = "PR_OPENED"
    REVIEW_RUNNING = "REVIEW_RUNNING"
    VERIFICATION_RUNNING = "VERIFICATION_RUNNING"
    GOVERNANCE_REQUESTED = "GOVERNANCE_REQUESTED"
    WAITING_OPERATOR_APPROVAL = "WAITING_OPERATOR_APPROVAL"
    APPLYING = "APPLYING"
    APPLIED = "APPLIED"
    POST_APPLY_VALIDATING = "POST_APPLY_VALIDATING"
    VERIFIED = "VERIFIED"
    ROLLBACK_REQUIRED = "ROLLBACK_REQUIRED"
    ROLLING_BACK = "ROLLING_BACK"
    ROLLED_BACK = "ROLLED_BACK"
    FAILED = "FAILED"
    MANUAL_REQUIRED = "MANUAL_REQUIRED"
    CANCELLED = "CANCELLED"

class AutoPatchSourceType(str, Enum):
    WAR_ROOM_ACTION = "WAR_ROOM_ACTION"
    SECURITY_FINDING = "SECURITY_FINDING"
    SLO_BREACH = "SLO_BREACH"
    MANUAL_TRIGGER = "MANUAL_TRIGGER"
    DRIFT_DETECTION = "DRIFT_DETECTION"

class PatchNegotiationStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    CONSENSUS_REACHED = "CONSENSUS_REACHED"
    DISAGREEMENT = "DISAGREEMENT"
    MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class PatchAgentOpinionType(str, Enum):
    SUPPORT = "SUPPORT"
    OPPOSE = "OPPOSE"
    WARNING = "WARNING"
    REQUEST_MORE_EVIDENCE = "REQUEST_MORE_EVIDENCE"
    REQUIRE_MANUAL_REVIEW = "REQUIRE_MANUAL_REVIEW"

class PatchDebateTurnType(str, Enum):
    PROPOSAL = "PROPOSAL"
    CRITIQUE = "CRITIQUE"
    DEFENSE = "DEFENSE"
    VERIFIER_FEEDBACK = "VERIFIER_FEEDBACK"
    RISK_WARNING = "RISK_WARNING"
    COST_WARNING = "COST_WARNING"
    FINAL_VOTE = "FINAL_VOTE"

class PatchSelectionDecisionType(str, Enum):
    SELECTED_FOR_GOVERNANCE = "SELECTED_FOR_GOVERNANCE"
    REQUIRE_MANUAL_REVIEW = "REQUIRE_MANUAL_REVIEW"
    REJECT_ALL = "REJECT_ALL"
    REQUEST_NEW_CANDIDATE = "REQUEST_NEW_CANDIDATE"
    BLOCKED_BY_POLICY = "BLOCKED_BY_POLICY"
    BLOCKED_BY_COGNITIVE_INTEGRITY = "BLOCKED_BY_COGNITIVE_INTEGRITY"

class UIAutoPatchExecution(Base):
    """Phase 27: Orchestrates a single autonomous remediation cycle."""
    __tablename__ = "ui_autopatch_executions"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    execution_key: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    source_type: Mapped[AutoPatchSourceType] = mapped_column(SAEnum(AutoPatchSourceType))
    source_id: Mapped[uuid.UUID | None] = mapped_column(GUID)

    war_room_id: Mapped[uuid.UUID | None] = mapped_column(GUID, ForeignKey("ui_incident_war_rooms.id"))
    action_item_id: Mapped[uuid.UUID | None] = mapped_column(GUID, ForeignKey("ui_incident_action_items.id"))
    remediation_plan_id: Mapped[uuid.UUID | None] = mapped_column(GUID)

    status: Mapped[AutoPatchExecutionStatus] = mapped_column(SAEnum(AutoPatchExecutionStatus), default=AutoPatchExecutionStatus.PLANNED)
    risk_level: Mapped[UIRepairSeverity] = mapped_column(SAEnum(UIRepairSeverity), default=UIRepairSeverity.MEDIUM)

    patch_strategy: Mapped[str | None] = mapped_column(String(64))
    patch_path: Mapped[str | None] = mapped_column(String(512))
    pr_url: Mapped[str | None] = mapped_column(String(512))
    branch_name: Mapped[str | None] = mapped_column(String(255))

    governance_approval_id: Mapped[uuid.UUID | None] = mapped_column(GUID)
    rollback_snapshot_path: Mapped[str | None] = mapped_column(String(512))

    error_message: Mapped[str | None] = mapped_column(Text)
    evidence_hash: Mapped[str | None] = mapped_column(String(128))

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIPatchCandidate(Base):
    """Phase 27: A potential fix candidate generated during planning."""
    __tablename__ = "ui_patch_candidates"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    execution_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("ui_autopatch_executions.id"))

    candidate_key: Mapped[str] = mapped_column(String(64))
    strategy: Mapped[str] = mapped_column(String(64))

    affected_files_json: Mapped[list[str]] = mapped_column(SmartJSON(), default=list)
    affected_routes_json: Mapped[list[str]] = mapped_column(SmartJSON(), default=list)

    summary: Mapped[str] = mapped_column(Text)
    risk_level: Mapped[str] = mapped_column(String(32))

    cognitive_integrity_score: Mapped[float] = mapped_column(Float, default=1.0)
    pr_agent_score: Mapped[float] = mapped_column(Float, default=1.0)
    verifier_score: Mapped[float] = mapped_column(Float, default=0.0)

    selected: Mapped[bool] = mapped_column(Boolean, default=False)
    rejected_reason: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIVerificationRunV2(Base):
    """Phase 27: Detailed verification metrics for an execution."""
    __tablename__ = "ui_verification_runs_v2"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    execution_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("ui_autopatch_executions.id"))

    status: Mapped[str] = mapped_column(String(32)) # PASSED, FAILED, RUNNING

    lint_status: Mapped[str] = mapped_column(String(16))
    typecheck_status: Mapped[str] = mapped_column(String(16))
    unit_test_status: Mapped[str] = mapped_column(String(16))
    build_status: Mapped[str] = mapped_column(String(16))
    playwright_status: Mapped[str] = mapped_column(String(16))
    affected_route_status: Mapped[str] = mapped_column(String(16))
    security_posture_status: Mapped[str] = mapped_column(String(16))
    cognitive_integrity_status: Mapped[str] = mapped_column(String(16))

    result_summary_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    logs_path: Mapped[str | None] = mapped_column(String(512))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIPostApplyValidation(Base):
    """Phase 27: Health and security validation after applying a patch."""
    __tablename__ = "ui_post_apply_validations"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    execution_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("ui_autopatch_executions.id"))

    status: Mapped[str] = mapped_column(String(32)) # PASSED, FAILED

    route_health_after_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    posture_score_before: Mapped[float] = mapped_column(Float)
    posture_score_after: Mapped[float] = mapped_column(Float)

    evidence_chain_valid: Mapped[bool] = mapped_column(Boolean, default=True)
    regression_passed: Mapped[bool] = mapped_column(Boolean, default=True)
    rollback_required: Mapped[bool] = mapped_column(Boolean, default=False)

    residual_risk: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIRollbackExecution(Base):
    """Phase 27: Records a rollback event if validation fails."""
    __tablename__ = "ui_rollback_executions"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    execution_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("ui_autopatch_executions.id"))

    status: Mapped[str] = mapped_column(String(32)) # SUCCESS, FAILED
    rollback_reason: Mapped[str] = mapped_column(Text)
    rollback_snapshot_path: Mapped[str] = mapped_column(String(512))

    rollback_result_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)

    evidence_hash: Mapped[str | None] = mapped_column(String(128))

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIAutoPatchTrace(Base):
    """Phase 28: Collects observability traces for Auto-Patch executions."""
    __tablename__ = "ui_autopatch_traces"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    execution_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("ui_autopatch_executions.id"))

    step_name: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32))

    duration_ms: Mapped[int | None] = mapped_column(Integer)
    agent_name: Mapped[str | None] = mapped_column(String(128))

    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    token_input: Mapped[int] = mapped_column(Integer, default=0)
    token_output: Mapped[int] = mapped_column(Integer, default=0)

    error_message: Mapped[str | None] = mapped_column(Text)
    evidence_hash: Mapped[str | None] = mapped_column(String(128))

    metadata_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIPatchAgentOpinion(Base):
    """Phase 28: Stores opinions of different agents about a patch candidate."""
    __tablename__ = "ui_patch_agent_opinions"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    execution_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("ui_autopatch_executions.id"))
    candidate_id: Mapped[uuid.UUID | None] = mapped_column(GUID, ForeignKey("ui_patch_candidates.id"))

    agent_name: Mapped[str] = mapped_column(String(128))
    opinion_type: Mapped[PatchAgentOpinionType] = mapped_column(SAEnum(PatchAgentOpinionType))

    score: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    rationale: Mapped[str | None] = mapped_column(Text)

    concerns_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    recommendation: Mapped[str | None] = mapped_column(String(256))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIPatchNegotiationSession(Base):
    """Phase 28: Orchestrates the multi-agent debate session."""
    __tablename__ = "ui_patch_negotiation_sessions"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    execution_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("ui_autopatch_executions.id"))

    status: Mapped[PatchNegotiationStatus] = mapped_column(SAEnum(PatchNegotiationStatus), default=PatchNegotiationStatus.PENDING)

    participant_agents_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    candidate_count: Mapped[int] = mapped_column(Integer, default=0)
    selected_candidate_id: Mapped[uuid.UUID | None] = mapped_column(GUID, ForeignKey("ui_patch_candidates.id"))

    consensus_score: Mapped[float] = mapped_column(Float, default=0.0)
    disagreement_score: Mapped[float] = mapped_column(Float, default=0.0)

    final_rationale: Mapped[str | None] = mapped_column(Text)
    evidence_hash: Mapped[str | None] = mapped_column(String(128))

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIPatchDebateTurn(Base):
    """Phase 28: Individual turns in the negotiation debate."""
    __tablename__ = "ui_patch_debate_turns"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    negotiation_session_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("ui_patch_negotiation_sessions.id"))

    agent_name: Mapped[str] = mapped_column(String(128))
    candidate_id: Mapped[uuid.UUID | None] = mapped_column(GUID, ForeignKey("ui_patch_candidates.id"))

    turn_type: Mapped[PatchDebateTurnType] = mapped_column(SAEnum(PatchDebateTurnType))
    message: Mapped[str] = mapped_column(Text)

    claims_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    evidence_refs_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)

    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIPatchCandidateScore(Base):
    """Phase 28: Comprehensive scoring for patch candidates."""
    __tablename__ = "ui_patch_candidate_scores"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("ui_patch_candidates.id"))
    execution_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("ui_autopatch_executions.id"))

    safety_score: Mapped[float] = mapped_column(Float, default=0.0)
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    test_score: Mapped[float] = mapped_column(Float, default=0.0)
    cognitive_integrity_score: Mapped[float] = mapped_column(Float, default=0.0)
    policy_score: Mapped[float] = mapped_column(Float, default=0.0)
    cost_score: Mapped[float] = mapped_column(Float, default=0.0)
    maintainability_score: Mapped[float] = mapped_column(Float, default=0.0)
    rollback_safety_score: Mapped[float] = mapped_column(Float, default=0.0)

    total_score: Mapped[float] = mapped_column(Float, default=0.0)
    scoring_rationale: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIPatchSelectionDecision(Base):
    """Phase 28: Final decision on which candidate to select."""
    __tablename__ = "ui_patch_selection_decisions"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    execution_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("ui_autopatch_executions.id"))
    negotiation_session_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("ui_patch_negotiation_sessions.id"))

    selected_candidate_id: Mapped[uuid.UUID | None] = mapped_column(GUID, ForeignKey("ui_patch_candidates.id"))
    decision: Mapped[PatchSelectionDecisionType] = mapped_column(SAEnum(PatchSelectionDecisionType))

    reason: Mapped[str | None] = mapped_column(Text)
    rejected_candidates_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    operator_visible_explanation: Mapped[str | None] = mapped_column(Text)

    evidence_hash: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

# --- Phase 29: Knowledge Graph + Causal Memory + Long-Term System Learning ---

class KnowledgeNodeType(str, enum.Enum):
    INCIDENT = "INCIDENT"
    WAR_ROOM = "WAR_ROOM"
    SECURITY_FINDING = "SECURITY_FINDING"
    RED_TEAM_FINDING = "RED_TEAM_FINDING"
    THREAT_MODEL = "THREAT_MODEL"
    ATTACK_PATH = "ATTACK_PATH"
    REMEDIATION_PLAN = "REMEDIATION_PLAN"
    AUTOPATCH_EXECUTION = "AUTOPATCH_EXECUTION"
    PATCH_CANDIDATE = "PATCH_CANDIDATE"
    POLICY_RULE = "POLICY_RULE"
    POLICY_DECISION = "POLICY_DECISION"
    IDENTITY = "IDENTITY"
    TOOL_CALL = "TOOL_CALL"
    MCP_SERVER = "MCP_SERVER"
    TENANT = "TENANT"
    CLUSTER = "CLUSTER"
    EVIDENCE_RECORD = "EVIDENCE_RECORD"
    SLO_BREACH = "SLO_BREACH"
    COST_ANOMALY = "COST_ANOMALY"
    COGNITIVE_FINDING = "COGNITIVE_FINDING"
    MESH_FAILOVER = "MESH_FAILOVER"
    GUARDRAIL_TUNING = "GUARDRAIL_TUNING"

class KnowledgeEdgeType(str, enum.Enum):
    CAUSED_BY = "CAUSED_BY"
    TRIGGERED = "TRIGGERED"
    MITIGATED_BY = "MITIGATED_BY"
    FAILED_TO_FIX = "FAILED_TO_FIX"
    RECURRED_AFTER = "RECURRED_AFTER"
    SIMILAR_TO = "SIMILAR_TO"
    DEPENDS_ON = "DEPENDS_ON"
    VIOLATED_POLICY = "VIOLATED_POLICY"
    USED_TOOL = "USED_TOOL"
    AFFECTED_TENANT = "AFFECTED_TENANT"
    AFFECTED_CLUSTER = "AFFECTED_CLUSTER"
    PRODUCED_EVIDENCE = "PRODUCED_EVIDENCE"
    SELECTED_CANDIDATE = "SELECTED_CANDIDATE"
    REJECTED_CANDIDATE = "REJECTED_CANDIDATE"
    IMPROVED_SCORE = "IMPROVED_SCORE"
    DEGRADED_SCORE = "DEGRADED_SCORE"

class IncidentPatternType(str, enum.Enum):
    RECURRING_INCIDENT = "RECURRING_INCIDENT"
    RECURRING_POLICY_DRIFT = "RECURRING_POLICY_DRIFT"
    RECURRING_TOOL_FAILURE = "RECURRING_TOOL_FAILURE"
    RECURRING_COGNITIVE_BLOCK = "RECURRING_COGNITIVE_BLOCK"
    RECURRING_PATCH_FAILURE = "RECURRING_PATCH_FAILURE"
    RECURRING_MESH_DEGRADATION = "RECURRING_MESH_DEGRADATION"
    RECURRING_COST_SPIKE = "RECURRING_COST_SPIKE"
    RECURRING_TENANT_ISOLATION_RISK = "RECURRING_TENANT_ISOLATION_RISK"
    SUCCESSFUL_REMEDIATION_PATTERN = "SUCCESSFUL_REMEDIATION_PATTERN"
    FAILED_REMEDIATION_PATTERN = "FAILED_REMEDIATION_PATTERN"

class UIKnowledgeNode(Base):
    """Phase 29: Unified knowledge graph node."""
    __tablename__ = "ui_knowledge_nodes"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    node_key: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    node_type: Mapped[str] = mapped_column(String(64), index=True)

    source_type: Mapped[str] = mapped_column(String(64), index=True)
    source_id: Mapped[str | None] = mapped_column(String(255), index=True)

    tenant_key: Mapped[str | None] = mapped_column(String(64), index=True)
    project_key: Mapped[str | None] = mapped_column(String(64), index=True)
    cluster_key: Mapped[str | None] = mapped_column(String(64), index=True)

    title: Mapped[str] = mapped_column(String(255))
    summary: Mapped[str | None] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(32), default="INFO")
    confidence: Mapped[float] = mapped_column(Float, default=1.0)

    metadata_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default={})

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class UIKnowledgeEdge(Base):
    """Phase 29: Relationships between knowledge nodes."""
    __tablename__ = "ui_knowledge_edges"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    source_node_key: Mapped[str] = mapped_column(String(255), index=True)
    target_node_key: Mapped[str] = mapped_column(String(255), index=True)
    edge_type: Mapped[str] = mapped_column(String(64), index=True)

    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    evidence_refs_json: Mapped[list[str]] = mapped_column(SmartJSON(), default=[])
    metadata_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default={})

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UICausalMemory(Base):
    """Phase 29: Long-term causal learning storage."""
    __tablename__ = "ui_causal_memories"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    memory_key: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    pattern_type: Mapped[str] = mapped_column(String(64), index=True)

    root_cause: Mapped[str] = mapped_column(Text)
    trigger_conditions_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON())
    action_taken_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON())
    outcome_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON())

    success_score: Mapped[float] = mapped_column(Float)
    recurrence_count: Mapped[int] = mapped_column(Integer, default=1)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)

    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class UICausalChain(Base):
    """Phase 29: Reconstructed causal chains for specific incidents."""
    __tablename__ = "ui_causal_chains"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    chain_key: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    incident_id: Mapped[uuid.UUID | None] = mapped_column(GUID, index=True)
    war_room_id: Mapped[uuid.UUID | None] = mapped_column(GUID, index=True)

    root_node_key: Mapped[str] = mapped_column(String(255))
    terminal_node_key: Mapped[str] = mapped_column(String(255))

    chain_json: Mapped[list[dict[str, Any]]] = mapped_column(SmartJSON()) # List of edges/nodes
    causal_confidence: Mapped[float] = mapped_column(Float, default=1.0)
    summary: Mapped[str | None] = mapped_column(Text)

    evidence_hash: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIIncidentPattern(Base):
    """Phase 29: Mined patterns of recurring incidents/failures."""
    __tablename__ = "ui_incident_patterns"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    pattern_key: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    pattern_type: Mapped[str] = mapped_column(String(64), index=True)
    affected_domain: Mapped[str] = mapped_column(String(128))

    recurrence_count: Mapped[int] = mapped_column(Integer, default=1)
    example_incidents_json: Mapped[list[str]] = mapped_column(SmartJSON(), default=[])
    common_root_causes_json: Mapped[list[str]] = mapped_column(SmartJSON(), default=[])

    successful_remediations_json: Mapped[list[str]] = mapped_column(SmartJSON(), default=[])
    failed_remediations_json: Mapped[list[str]] = mapped_column(SmartJSON(), default=[])

    recommended_action: Mapped[str | None] = mapped_column(Text)
    risk_level: Mapped[str] = mapped_column(String(32), default="MEDIUM")
    confidence: Mapped[float] = mapped_column(Float, default=1.0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class UISimilarCaseMatch(Base):
    """Phase 29: Similarity matches between current and historical cases."""
    __tablename__ = "ui_similar_case_matches"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    query_source_type: Mapped[str] = mapped_column(String(64), index=True)
    query_source_id: Mapped[str] = mapped_column(String(255), index=True)

    matched_source_type: Mapped[str] = mapped_column(String(64))
    matched_source_id: Mapped[str] = mapped_column(String(255))

    similarity_score: Mapped[float] = mapped_column(Float)
    matched_features_json: Mapped[list[str]] = mapped_column(SmartJSON(), default=[])
    recommended_action: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIRiskPrediction(Base):
    """Phase 29: AI-predicted future risks based on patterns."""
    __tablename__ = "ui_risk_predictions"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    prediction_key: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    target_type: Mapped[str] = mapped_column(String(64), index=True) # tenant, project, cluster, tool, identity, route, policy
    target_key: Mapped[str] = mapped_column(String(255), index=True)

    risk_type: Mapped[str] = mapped_column(String(64), index=True)
    probability: Mapped[float] = mapped_column(Float)
    severity: Mapped[str] = mapped_column(String(32), default="MEDIUM")

    predicted_window: Mapped[str] = mapped_column(String(64)) # e.g. "NEXT_24H", "NEXT_7D"
    contributing_factors_json: Mapped[list[str]] = mapped_column(SmartJSON(), default=[])
    recommended_prevention: Mapped[str | None] = mapped_column(Text)

    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

# --- Phase 30: Final Integration + Production Hardening + Release Lock ---

class ReleaseStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    WARNING = "WARNING"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    SEALED = "SEALED"
    RELEASE_CANDIDATE = "RELEASE_CANDIDATE"

class UIFinalIntegrationAudit(Base):
    """Phase 30: End-to-end integration audit for all modules."""
    __tablename__ = "ui_final_integration_audits"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    audit_key: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    status: Mapped[ReleaseStatus] = mapped_column(SAEnum(ReleaseStatus), default=ReleaseStatus.PENDING)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    checked_modules_json: Mapped[dict[str, str]] = mapped_column(SmartJSON(), default=dict)
    failed_modules_json: Mapped[list[str]] = mapped_column(SmartJSON(), default=list)
    warnings_json: Mapped[list[str]] = mapped_column(SmartJSON(), default=list)
    summary_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)

    evidence_hash: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIReleaseReadinessCheck(Base):
    """Phase 30: Readiness evaluation against production standards."""
    __tablename__ = "ui_release_readiness_checks"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    check_key: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(64), index=True) # API, DB, UI, Security, etc.
    status: Mapped[ReleaseStatus] = mapped_column(SAEnum(ReleaseStatus), default=ReleaseStatus.PENDING)

    score: Mapped[float] = mapped_column(Float, default=0.0)
    blockers_json: Mapped[list[str]] = mapped_column(SmartJSON(), default=list)
    warnings_json: Mapped[list[str]] = mapped_column(SmartJSON(), default=list)
    recommendation: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIFinalAuditPack(Base):
    """Phase 30: Comprehensive audit package for production release."""
    __tablename__ = "ui_final_audit_packs"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    pack_key: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    status: Mapped[ReleaseStatus] = mapped_column(SAEnum(ReleaseStatus), default=ReleaseStatus.PENDING)

    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    version: Mapped[str] = mapped_column(String(64))

    included_sections_json: Mapped[list[str]] = mapped_column(SmartJSON(), default=list)
    residual_risks_json: Mapped[list[dict[str, Any]]] = mapped_column(SmartJSON(), default=list)
    known_limitations_json: Mapped[list[str]] = mapped_column(SmartJSON(), default=list)
    summary_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)

    evidence_hash: Mapped[str | None] = mapped_column(String(255))
    report_path: Mapped[str | None] = mapped_column(String(512))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIReleaseLock(Base):
    """Phase 30: Final immutable lock for a release candidate."""
    __tablename__ = "ui_release_locks"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    release_key: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    version: Mapped[str] = mapped_column(String(64))
    status: Mapped[ReleaseStatus] = mapped_column(SAEnum(ReleaseStatus), default=ReleaseStatus.SEALED)

    locked_by: Mapped[str] = mapped_column(String(128))
    locked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    commit_sha: Mapped[str | None] = mapped_column(String(128))

    test_summary_json: Mapped[dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    audit_pack_id: Mapped[uuid.UUID | None] = mapped_column(GUID, ForeignKey("ui_final_audit_packs.id"))
    release_notes: Mapped[str | None] = mapped_column(Text)

    evidence_hash: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIResidualRiskAcceptance(Base):
    """Phase 30: Persistent operator acceptance record for a residual risk."""
    __tablename__ = "ui_residual_risk_acceptances"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    risk_id: Mapped[str] = mapped_column(String(64), index=True)
    risk_fingerprint: Mapped[str] = mapped_column(String(128), unique=True, index=True)

    module: Mapped[str] = mapped_column(String(128))
    severity: Mapped[str] = mapped_column(String(32))
    description: Mapped[str] = mapped_column(Text)
    mitigation: Mapped[str] = mapped_column(Text)
    mitigation_strategy: Mapped[str] = mapped_column(Text)

    operator: Mapped[str] = mapped_column(String(128), index=True)
    operator_rationale: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="ACCEPTED")

    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
