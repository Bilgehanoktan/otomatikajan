import enum
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy import Column, String, Text, Integer, Float, DateTime, ForeignKey, Boolean, Enum as SAEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from libs.db.base import Base, GUID, SmartJSON, utcnow

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
    assigned_to: Mapped[Optional[str]] = mapped_column(String(128)) # User ID or Team
    
    notification_channels_json: Mapped[List[str]] = mapped_column(SmartJSON(), default=list) # ['DASHBOARD', 'EMAIL', 'TELEGRAM']
    notification_status_json: Mapped[Dict[str, Any]] = mapped_column(SmartJSON(), default=dict) # { 'EMAIL': 'SENT', 'TELEGRAM': 'FAILED' }
    
    acknowledged_by: Mapped[Optional[str]] = mapped_column(String(128))
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    resolved_by: Mapped[Optional[str]] = mapped_column(String(128))
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
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
    provider_response_json: Mapped[Dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    failed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
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

class UIRedTeamScenario(Base):
    """AI-generated adversarial scenarios to test system robustness."""
    __tablename__ = "ui_red_team_scenarios"

    id          = Column(GUID, primary_key=True, default=uuid.uuid4)
    name        = Column(String(128), nullable=False)
    description = Column(Text)
    risk_type   = Column(String(64)) # governance_bypass, repair_loop, etc.
    
    expected_detection = Column(String(64))
    expected_severity  = Column(String(32))
    expected_policy_decision = Column(String(64))
    
    is_destructive = Column(Boolean, default=False)
    created_at     = Column(DateTime(timezone=True), default=utcnow)

class UIRedTeamRun(Base):
    """Execution results of Red Team scenarios."""
    __tablename__ = "ui_red_team_runs"

    id          = Column(GUID, primary_key=True, default=uuid.uuid4)
    scenario_id = Column(GUID, ForeignKey("ui_red_team_scenarios.id"))
    status      = Column(String(32), default="PENDING")
    
    actual_detection = Column(String(64))
    actual_severity  = Column(String(32))
    actual_decision  = Column(String(64))
    
    passed          = Column(Boolean, default=False)
    vulnerability_found = Column(Boolean, default=False)
    findings_json   = Column(SmartJSON(), default=dict)
    
    started_at  = Column(DateTime(timezone=True), default=utcnow)
    finished_at = Column(DateTime(timezone=True))

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

class UIFinalAuditPack(Base):
    """Aggregated evidence and governance documents for external audit."""
    __tablename__ = "ui_final_audit_packs"

    id          = Column(GUID, primary_key=True, default=uuid.uuid4)
    name        = Column(String(128))
    version     = Column(String(32))
    
    summary_report_path = Column(String(512))
    evidence_bundle_hash = Column(String(128))
    
    content_manifest_json = Column(SmartJSON(), default=dict)
    
    is_sealed   = Column(Boolean, default=True)
    created_at  = Column(DateTime(timezone=True), default=utcnow)

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
    responsibilities_json: Mapped[List[str]] = mapped_column(SmartJSON(), default=list)
    owned_project_keys_json: Mapped[List[str]] = mapped_column(SmartJSON(), default=list)
    escalation_channels_json: Mapped[Dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    oncall_policy_json: Mapped[Dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
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
    backup_owner: Mapped[Optional[str]] = mapped_column(String(255))
    approval_policy_json: Mapped[Dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class UIMaintenancePolicy(Base):
    """Project-specific maintenance windows and allowed automated actions."""
    __tablename__ = "ui_maintenance_policies"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    project_key: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    policy_name: Mapped[str] = mapped_column(String(128), nullable=False)
    maintenance_window_json: Mapped[Dict[str, Any]] = mapped_column(SmartJSON(), default=dict) # { "start_time": "02:00", "end_time": "05:00", "days": [0,6] }
    allowed_actions_json: Mapped[List[str]] = mapped_column(SmartJSON(), default=list)
    blocked_actions_json: Mapped[List[str]] = mapped_column(SmartJSON(), default=list)
    
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
    release_type: Mapped[Optional[str]] = mapped_column(String(32)) # PATCH, MINOR, MAJOR, HOTFIX, ROLLBACK, POLICY_UPDATE
    project_keys_json: Mapped[List[str]] = mapped_column(SmartJSON(), default=list)
    
    summary: Mapped[Optional[str]] = mapped_column(Text)
    changes_json: Mapped[List[Dict[str, Any]]] = mapped_column(SmartJSON(), default=list)
    risk_summary_json: Mapped[Dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    compatibility_notes: Mapped[Optional[str]] = mapped_column(Text)
    rollback_notes: Mapped[Optional[str]] = mapped_column(Text)
    evidence_hash: Mapped[Optional[str]] = mapped_column(String(255))
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UICompatibilityCheck(Base):
    """Result of compatibility validation for routes and policies."""
    __tablename__ = "ui_compatibility_checks"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    project_key: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    version: Mapped[Optional[str]] = mapped_column(String(32))
    status: Mapped[Optional[str]] = mapped_column(String(32)) # PASSED, WARNING, FAILED
    
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    breaking_changes_json: Mapped[List[str]] = mapped_column(SmartJSON(), default=list)
    deprecated_features_json: Mapped[List[str]] = mapped_column(SmartJSON(), default=list)
    migration_required: Mapped[bool] = mapped_column(Boolean, default=False)
    migration_notes: Mapped[Optional[str]] = mapped_column(Text)
    evidence_hash: Mapped[Optional[str]] = mapped_column(String(255))

class UISLOBreach(Base):
    """Detection and tracking of SLO violations."""
    __tablename__ = "ui_slo_breaches"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    project_key: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    slo_name: Mapped[str] = mapped_column(String(128), nullable=False)
    severity: Mapped[Optional[str]] = mapped_column(String(32)) # WARNING, CRITICAL
    observed_value: Mapped[Optional[float]] = mapped_column(Float)
    target_value: Mapped[Optional[float]] = mapped_column(Float)
    
    breach_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    breach_resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), default="OPEN") # OPEN, ACKNOWLEDGED, MITIGATING, RESOLVED, WAIVED
    
    linked_incident_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID, nullable=True)
    remediation_plan_json: Mapped[Dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIEvidenceRetentionPolicy(Base):
    """Lifecycle policy for autonomous repair evidence."""
    __tablename__ = "ui_evidence_retention_policies"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    policy_name: Mapped[str] = mapped_column(String(128), nullable=False)
    retention_days: Mapped[int] = mapped_column(Integer, default=365)
    evidence_type: Mapped[Optional[str]] = mapped_column(String(64)) # monitoring, repair, governance, chaos, pilot, release
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
    owner: Mapped[Optional[str]] = mapped_column(String(255))
    
    route_scope_json: Mapped[List[str]] = mapped_column(SmartJSON(), default=list)
    critical_routes_json: Mapped[List[str]] = mapped_column(SmartJSON(), default=list)
    safety_policy_json: Mapped[Dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    governance_policy_json: Mapped[Dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    
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
    
    project_keys_json: Mapped[List[str]] = mapped_column(SmartJSON(), default=list)
    rollout_mode: Mapped[str] = mapped_column(String(32), default="GOVERNED_REPAIR")
    
    success_criteria_json: Mapped[Dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    failure_criteria_json: Mapped[Dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    summary_json: Mapped[Dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class UIProjectHealthSnapshot(Base):
    """Point-in-time health metrics for a project."""
    __tablename__ = "ui_project_health_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    project_key: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    
    health_score: Mapped[float] = mapped_column(Float, default=100.0)
    monitoring_status: Mapped[Optional[str]] = mapped_column(String(32))
    
    open_cases: Mapped[int] = mapped_column(Integer, default=0)
    critical_cases: Mapped[int] = mapped_column(Integer, default=0)
    governance_waiting: Mapped[int] = mapped_column(Integer, default=0)
    active_repairs: Mapped[int] = mapped_column(Integer, default=0)
    
    last_incident_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    sla_status: Mapped[Optional[str]] = mapped_column(String(32))
    slo_status: Mapped[Optional[str]] = mapped_column(String(32))
    
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
    
    blockers_json: Mapped[List[str]] = mapped_column(SmartJSON(), default=list)
    warnings_json: Mapped[List[str]] = mapped_column(SmartJSON(), default=list)
    
    recommendation: Mapped[Optional[str]] = mapped_column(String(32)) # GA_READY, GA_WITH_WARNINGS, LIMITED_GA, EXTEND_PILOT, NO_GO
    assessed_by: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIEnterpriseRunbook(Base):
    """Automatically generated operating guide for enterprise deployment."""
    __tablename__ = "ui_enterprise_runbooks"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    scope: Mapped[Optional[str]] = mapped_column(String(128))
    
    content: Mapped[Optional[str]] = mapped_column(Text)
    evidence_hash: Mapped[Optional[str]] = mapped_column(String(255))
    
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

# Phase 14: Enterprise FinOps + Capacity Planning + Cost-Aware Autonomy Models

class UICostEvent(Base):
    """Granular tracking of every agent/LLM/tool call and its associated cost."""
    __tablename__ = "ui_cost_events"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    project_key: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    team_key: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    tenant_key: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    cluster_key: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    
    source_type: Mapped[str] = mapped_column(String(64)) # AGENT, TOOL, MONITORING, REPAIR
    source_id: Mapped[Optional[str]] = mapped_column(String(128)) # case_id, drill_id, etc.
    operation_type: Mapped[str] = mapped_column(String(64), index=True) # MONITORING_RUN, STAGEHAND_DIAGNOSTIC, etc.
    
    provider: Mapped[Optional[str]] = mapped_column(String(64)) # OPENAI, ANTHROPIC, OPENROUTER
    model: Mapped[Optional[str]] = mapped_column(String(128))
    
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    tool_calls: Mapped[int] = mapped_column(Integer, default=0)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    
    estimated_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIBudgetPolicy(Base):
    """Financial guardrails for projects and teams."""
    __tablename__ = "ui_budget_policies"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    project_key: Mapped[Optional[str]] = mapped_column(String(64), unique=True, index=True)
    team_key: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    tenant_key: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    cluster_key: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    
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
    
    reason: Mapped[Optional[str]] = mapped_column(Text)
    linked_event_ids_json: Mapped[List[str]] = mapped_column(SmartJSON(), default=list)
    
    status: Mapped[str] = mapped_column(String(32), default="OPEN") # OPEN, ACKNOWLEDGED, RESOLVED, WAIVED
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

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
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    expected_savings_usd: Mapped[float] = mapped_column(Float, default=0.0)
    risk_impact: Mapped[str] = mapped_column(String(32), default="LOW") # NONE, LOW, MEDIUM, HIGH
    
    status: Mapped[str] = mapped_column(String(32), default="PENDING") # PENDING, APPLIED, REJECTED, IGNORED
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    applied_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

# --- Phase 15: Autonomous Ecosystem Governance + Policy-as-Code (PaC) Models ---

class UIPolicyRule(Base):
    """Represents a Policy-as-Code rule that governs autonomous behavior."""
    __tablename__ = "ui_policy_rules"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    policy_key: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    scope: Mapped[str] = mapped_column(String(32), default="GLOBAL") # GLOBAL, TENANT, CLUSTER, PROJECT, TEAM, ROUTE, ACTION
    tenant_key: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    cluster_key: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    project_key: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    
    rule_type: Mapped[str] = mapped_column(String(64), default="AUTO_REPAIR") # AUTO_REPAIR, AUTO_APPLY, etc.
    priority: Mapped[int] = mapped_column(Integer, default=100)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    
    rule_definition_json: Mapped[Dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    created_by: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class UIPolicyEvaluation(Base):
    """Audit trail for every policy evaluation performed by the engine."""
    __tablename__ = "ui_policy_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    policy_key: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    tenant_key: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    cluster_key: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    project_key: Mapped[str] = mapped_column(String(64), index=True)
    
    action_type: Mapped[str] = mapped_column(String(64)) # e.g., 'APPROVE_AND_APPLY'
    target_type: Mapped[Optional[str]] = mapped_column(String(64))
    target_id: Mapped[Optional[str]] = mapped_column(String(64))
    
    decision: Mapped[str] = mapped_column(String(32)) # ALLOW, DENY, REQUIRE_APPROVAL, etc.
    reason: Mapped[Optional[str]] = mapped_column(Text)
    
    matched_rules_json: Mapped[Dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    input_context_json: Mapped[Dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    output_json: Mapped[Dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    
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
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

class UIPolicyProposal(Base):
    """Lifecycle for proposing and approving new governance policies."""
    __tablename__ = "ui_policy_proposals"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    proposal_type: Mapped[str] = mapped_column(String(64)) # NEW, UPDATE, DELETE
    policy_key: Mapped[str] = mapped_column(String(64))
    scope: Mapped[str] = mapped_column(String(32))
    tenant_key: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    cluster_key: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    project_key: Mapped[Optional[str]] = mapped_column(String(64))
    
    proposed_rule_json: Mapped[Dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    rationale: Mapped[str] = mapped_column(Text)
    risk_level: Mapped[str] = mapped_column(String(32)) # LOW, MEDIUM, HIGH, CRITICAL
    
    status: Mapped[str] = mapped_column(String(32), default="DRAFT") # DRAFT, SUBMITTED, APPROVED, etc.
    
    proposed_by: Mapped[str] = mapped_column(String(255))
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(255))
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIAutonomousOverride(Base):
    """Records manual overrides of blocked autonomous actions."""
    __tablename__ = "ui_autonomous_overrides"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    tenant_key: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    cluster_key: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    action_type: Mapped[str] = mapped_column(String(64))
    target_type: Mapped[str] = mapped_column(String(64))
    target_id: Mapped[str] = mapped_column(String(64))
    
    blocked_policy_key: Mapped[str] = mapped_column(String(64))
    override_reason: Mapped[str] = mapped_column(Text)
    operator: Mapped[str] = mapped_column(String(255))
    
    risk_level: Mapped[str] = mapped_column(String(32))
    approval_id: Mapped[Optional[str]] = mapped_column(String(64))
    evidence_hash: Mapped[Optional[str]] = mapped_column(String(255))
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIComplianceFinding(Base):
    """Audit of compliance violations found in the ecosystem."""
    __tablename__ = "ui_compliance_findings"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    tenant_key: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    cluster_key: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    project_key: Mapped[str] = mapped_column(String(64), index=True)
    source_type: Mapped[str] = mapped_column(String(64)) # e.g., 'PATCH', 'LOG', 'CONFIG'
    source_id: Mapped[str] = mapped_column(String(64))
    
    standard: Mapped[str] = mapped_column(String(64)) # INTERNAL_SECURITY, GDPR_LIKE, etc.
    severity: Mapped[str] = mapped_column(String(32)) # LOW, MEDIUM, HIGH, CRITICAL
    finding_type: Mapped[str] = mapped_column(String(64))
    
    description: Mapped[str] = mapped_column(Text)
    recommendation: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="OPEN") # OPEN, RESOLVED, DISMISSED
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

# --- Phase 16: Multi-Tenant Federation + Cross-Cluster Governance Models ---

class UITenantProfile(Base):
    """Phase 16: Multi-tenant organization profile."""
    __tablename__ = "ui_tenant_profiles"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    tenant_key: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    tenant_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE") # ACTIVE, SUSPENDED, DELETED
    governance_level: Mapped[str] = mapped_column(String(32), default="STANDARD") # STANDARD, STRICT, RELAXED
    
    contact_info: Mapped[Dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    tenant_metadata: Mapped[Dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    
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
    
    cluster_metadata: Mapped[Dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class UITenantProjectBinding(Base):
    """Phase 16: Mapping projects to tenants and clusters."""
    __tablename__ = "ui_tenant_project_bindings"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    tenant_key: Mapped[str] = mapped_column(String(64), ForeignKey("ui_tenant_profiles.tenant_key"), index=True)
    cluster_key: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("ui_cluster_profiles.cluster_key"), index=True, nullable=True)
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
    metrics_json: Mapped[Dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    
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
    cluster_key: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    project_key: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    
    policy_key: Mapped[str] = mapped_column(String(64), index=True)
    drift_type: Mapped[str] = mapped_column(String(64)) # RELAXED_RESTRICTION, DISABLED_GLOBAL_RULE, etc.
    drift_level: Mapped[str] = mapped_column(String(32), default="MEDIUM") # LOW, MEDIUM, HIGH, CRITICAL
    
    global_definition: Mapped[Dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    local_definition: Mapped[Dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    
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
    
    decision_json: Mapped[Dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    evidence_hash: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIGlobalLoadSteeringDecision(Base):
    """Phase 17: Audit trail for global workload steering decisions."""
    __tablename__ = "ui_global_load_steering_decisions"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    tenant_key: Mapped[str] = mapped_column(String(64), index=True)
    project_key: Mapped[str] = mapped_column(String(64), index=True)
    
    source_cluster_key: Mapped[Optional[str]] = mapped_column(String(64))
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
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    evidence_path: Mapped[Optional[str]] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIGlobalSLOSnapshot(Base):
    """Phase 17: Aggregated federation-wide SLO compliance snapshot."""
    __tablename__ = "ui_global_slo_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    tenant_key: Mapped[Optional[str]] = mapped_column(String(64), index=True) # None for Global
    
    federation_health_score: Mapped[float] = mapped_column(Float)
    global_mttr_s: Mapped[float] = mapped_column(Float)
    global_detection_latency_s: Mapped[float] = mapped_column(Float)
    
    repair_success_rate: Mapped[float] = mapped_column(Float)
    failover_success_rate: Mapped[float] = mapped_column(Float)
    policy_violation_count: Mapped[int] = mapped_column(Integer, default=0)
    evidence_sync_success_rate: Mapped[float] = mapped_column(Float)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class UIAutomatedPostmortem(Base):
    """Phase 17: LLM-generated incident post-mortem analysis."""
    __tablename__ = "ui_automated_postmortems"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    incident_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID, index=True)
    
    tenant_key: Mapped[str] = mapped_column(String(64), index=True)
    cluster_key: Mapped[str] = mapped_column(String(64), index=True)
    
    title: Mapped[str] = mapped_column(String(255))
    root_cause: Mapped[str] = mapped_column(Text)
    
    timeline_json: Mapped[Dict[str, Any]] = mapped_column(SmartJSON(), default=dict)
    impact_summary: Mapped[str] = mapped_column(Text)
    
    contributing_factors_json: Mapped[List[Dict[str, Any]]] = mapped_column(SmartJSON(), default=list)
    remediation_actions_json: Mapped[List[Dict[str, Any]]] = mapped_column(SmartJSON(), default=list)
    prevention_actions_json: Mapped[List[Dict[str, Any]]] = mapped_column(SmartJSON(), default=list)
    
    evidence_hash: Mapped[Optional[str]] = mapped_column(String(255))
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
