import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, Float, DateTime, ForeignKey, Boolean, Enum as SAEnum
from sqlalchemy.orm import relationship
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

    id          = Column(GUID, primary_key=True, default=uuid.uuid4)
    source_type = Column(String(64)) # MONITORING | CHAOS | AUTO_REPAIR_FAILURE
    source_id   = Column(GUID) # Case ID or Run ID
    
    route       = Column(String(256))
    severity    = Column(String(32)) # INFO | WATCH | OPERATOR_REVIEW | URGENT | CRITICAL | CRISIS
    escalation_level = Column(Integer, default=1)
    status      = Column(String(32), default="OPEN") # OPEN | NOTIFIED | ACKNOWLEDGED | IN_PROGRESS | RESOLVED | SUPPRESSED | ESCALATED | FAILED_TO_NOTIFY
    
    reason      = Column(Text)
    assigned_to = Column(String(128)) # User ID or Team
    
    notification_channels_json = Column(SmartJSON(), default=list) # ['DASHBOARD', 'EMAIL', 'TELEGRAM']
    notification_status_json   = Column(SmartJSON(), default=dict) # { 'EMAIL': 'SENT', 'TELEGRAM': 'FAILED' }
    
    acknowledged_by = Column(String(128))
    acknowledged_at = Column(DateTime(timezone=True))
    resolved_by     = Column(String(128))
    resolved_at     = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class UINotificationDelivery(Base):
    """Tracking individual notification delivery attempts."""
    __tablename__ = "ui_notification_deliveries"

    id            = Column(GUID, primary_key=True, default=uuid.uuid4)
    escalation_id = Column(GUID, ForeignKey("ui_operator_escalations.id"))
    
    channel       = Column(String(32)) # DASHBOARD | EMAIL | TELEGRAM | SLACK
    status        = Column(String(32)) # PENDING | SENT | FAILED | RETRYING
    recipient     = Column(String(256))
    
    title           = Column(String(256))
    message_summary = Column(Text)
    provider_response_json = Column(SmartJSON(), default=dict)
    
    sent_at   = Column(DateTime(timezone=True))
    failed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    
    created_at = Column(DateTime(timezone=True), default=utcnow)

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
