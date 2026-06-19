"""
Repair DB Modelleri — Self-Repair sisteminin kalıcı depolaması.

Tablolar:
- repair_incidents   : normalize edilmiş olay kayıtları
- repair_jobs        : pipeline durum makinesi
- repair_proposals   : PR önerileri (onay bekleniyor)
- repair_patch_log   : geçmiş patch sonuçları (hafıza)
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
)

from libs.db.base import GUID, Base, SmartJSON


def _utcnow():
    return datetime.now(UTC)


# ── Incident Kaydı ────────────────────────────────────────
class RepairIncident(Base):
    __tablename__ = "repair_incidents"

    id               = Column(GUID, primary_key=True, default=uuid.uuid4)
    incident_id      = Column(String(64), unique=True, nullable=False, index=True)
    source           = Column(String(32), nullable=False)      # runtime_log | ci_failure | ...
    severity         = Column(String(16), nullable=False, index=True)   # low|medium|high|critical
    service          = Column(String(64), nullable=False)
    module           = Column(String(128), nullable=False, index=True)
    symptom          = Column(Text, nullable=False)
    stack_trace      = Column(Text, default="")
    suspected_files  = Column(SmartJSON(), default=list)
    failing_tests    = Column(SmartJSON(), default=list)
    reproduction_hint = Column(Text, default="")
    context_data     = Column(SmartJSON(), default=dict)
    occurrence_count = Column(Integer, default=1)
    status           = Column(String(32), default="open", nullable=False, index=True)
    # open | triaged | in_repair | resolved | rejected
    first_seen_at    = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    last_seen_at     = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        Index("ix_repair_incidents_module_status", "module", "status"),
        Index("ix_repair_incidents_severity_status", "severity", "status"),
    )


# ── Repair Job (Durum Makinesi) ───────────────────────────
class RepairJobRecord(Base):
    __tablename__ = "repair_jobs"

    id             = Column(GUID, primary_key=True, default=uuid.uuid4)
    job_id         = Column(String(64), unique=True, nullable=False, index=True)
    incident_id    = Column(String(64), nullable=False, index=True)
    status         = Column(String(64), nullable=False, default="new", index=True)
    ticket_id      = Column(String(64), nullable=True)
    plan_id        = Column(String(64), nullable=True)
    validation_id  = Column(String(64), nullable=True)
    pr_url         = Column(String(512), nullable=True)
    branch_name    = Column(String(256), nullable=True)
    diff           = Column(Text, default="") # Text type has no practical limit
    error_detail   = Column(Text, default="")
    meta           = Column(SmartJSON(), default=dict)   # Faz 12+ tüm state
    history        = Column(SmartJSON(), default=list)   # durum geçiş log'u
    created_at     = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at     = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        Index("ix_repair_jobs_status_created", "status", "created_at"),
    )


# ── PR Önerisi ────────────────────────────────────────────
class RepairProposal(Base):
    __tablename__ = "repair_proposals"

    id                  = Column(GUID, primary_key=True, default=uuid.uuid4)
    pr_id               = Column(String(64), unique=True, nullable=False, index=True)
    job_id              = Column(String(64), nullable=False, index=True)
    incident_id         = Column(String(64), nullable=False)
    branch_name         = Column(String(256), nullable=False)
    title               = Column(String(512), nullable=False)
    body                = Column(Text, default="")
    diff                = Column(Text, default="")
    changed_files       = Column(SmartJSON(), default=list)
    risk_level          = Column(String(16), default="low")
    validation_summary  = Column(Text, default="")
    auto_merge          = Column(Boolean, default=False, nullable=False)
    # Durum
    decision            = Column(String(32), default="pending", nullable=False, index=True)
    # pending | approved | rejected | merged
    decided_by          = Column(String(128), default="")
    decided_at          = Column(DateTime(timezone=True), nullable=True)
    created_at          = Column(DateTime(timezone=True), default=_utcnow, nullable=False)


# ── Patch Hafızası (Öğrenme Logu) ────────────────────────
class RepairPatchLog(Base):
    __tablename__ = "repair_patch_logs"

    id               = Column(GUID, primary_key=True, default=uuid.uuid4)
    record_id        = Column(String(64), unique=True, nullable=False, index=True)
    job_id           = Column(String(64), nullable=False, index=True)
    incident_id      = Column(String(64), nullable=False)
    classification   = Column(String(64), nullable=False, index=True)
    target_files     = Column(SmartJSON(), default=list)
    diff_size_lines  = Column(Integer, default=0)
    outcome          = Column(String(32), nullable=False, index=True)
    # success | regression | rejected | manual_merged | rolled_back
    confidence       = Column(Integer, default=0)
    validation_score = Column(Integer, default=0)
    notes            = Column(Text, default="")
    recorded_at      = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    __table_args__ = (
        Index("ix_repair_patch_logs_class_outcome", "classification", "outcome"),
    )


# ── Vektör Hafıza (Deneyim Hafızası) ────────────────────
class VectorLessonModel(Base):
    __tablename__ = "repair_vector_lessons"

    id           = Column(GUID, primary_key=True, default=uuid.uuid4)
    lesson_id    = Column(String(64), unique=True, nullable=False, index=True)
    symptom      = Column(Text, nullable=False)
    module       = Column(String(128), nullable=False, index=True)
    resolution   = Column(Text, nullable=False)
    job_id       = Column(String(64), nullable=False)
    incident_id  = Column(String(64), nullable=False)
    embedding    = Column(SmartJSON(), default=list)  # TF-IDF veya LLM embedding
    tags         = Column(SmartJSON(), default=list)
    created_at   = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    __table_args__ = (
        Index("ix_repair_vector_lessons_module_created", "module", "created_at"),
    )


# ── Lab & Tournament Modelleri (Faz 28) ──────────────────

class RepairBenchmarkRun(Base):
    __tablename__ = "repair_benchmark_runs"

    id           = Column(GUID, primary_key=True, default=uuid.uuid4)
    run_id       = Column(String(64), unique=True, nullable=False, index=True)
    project_id   = Column(String(64), index=True) # Scope
    cluster_id   = Column(String(64), index=True)
    start_time   = Column(DateTime(timezone=True), default=_utcnow)
    end_time     = Column(DateTime(timezone=True))
    total_cases  = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    avg_score    = Column(Float, default=0.0)
    total_validation_cost = Column(Float, default=0.0)
    total_validation_time = Column(Float, default=0.0)
    status       = Column(String(32), default="running") # running | completed | failed


class RepairTournament(Base):
    __tablename__ = "repair_tournaments"

    id               = Column(GUID, primary_key=True, default=uuid.uuid4)
    tournament_id    = Column(String(64), unique=True, nullable=False, index=True)
    run_id           = Column(String(64), nullable=True, index=True)
    incident_id      = Column(String(64), nullable=False, index=True)
    project_id       = Column(String(64), index=True)
    cluster_id       = Column(String(64), index=True)
    winner_candidate_id = Column(String(64), nullable=True)
    winner_score     = Column(Float, default=0.0)
    verifier_score_breakdown = Column(SmartJSON(), default=dict) # Aggregate for winner
    total_candidates = Column(Integer, default=0)
    created_at       = Column(DateTime(timezone=True), default=_utcnow)


class RepairCandidate(Base):
    __tablename__ = "repair_candidates"

    id            = Column(GUID, primary_key=True, default=uuid.uuid4)
    candidate_id  = Column(String(64), unique=True, nullable=False, index=True)
    tournament_id = Column(String(64), nullable=False, index=True)
    strategy      = Column(String(32), nullable=False) # conservative | radical | etc
    candidate_type = Column(String(32))               # code | policy | config
    patch_diff    = Column(Text, nullable=False)
    patch_signature = Column(String(256), index=True) # for deduplication/memory
    risk_score    = Column(Float, default=0.0)
    final_score   = Column(Float, default=0.0)

    # Outcomes
    canary_outcome = Column(String(32))               # success | failure | rollback
    rollback_reason = Column(Text)

    # Metrics
    total_validation_cost = Column(Float, default=0.0)
    total_validation_time = Column(Float, default=0.0) # seconds

    status        = Column(String(32), default="draft") # draft | verified | winner | rejected


class VerifierResult(Base):
    __tablename__ = "verifier_results"

    id            = Column(GUID, primary_key=True, default=uuid.uuid4)
    result_id     = Column(String(64), unique=True, nullable=False, index=True)
    candidate_id  = Column(String(64), nullable=False, index=True)
    verifier_name = Column(String(64), nullable=False) # build | regression | economic etc
    score         = Column(Float, default=0.0)
    passed        = Column(Boolean, default=False)
    details       = Column(SmartJSON(), default=dict) # breakdown details
    timestamp     = Column(DateTime(timezone=True), default=_utcnow)


class RepairMemory(Base):
    __tablename__ = "repair_memories"

    id               = Column(GUID, primary_key=True, default=uuid.uuid4)
    memory_id        = Column(String(64), unique=True, nullable=False, index=True)
    incident_id      = Column(String(64), nullable=False, index=True)
    project_id       = Column(String(64), index=True)
    cluster_id       = Column(String(64), index=True)
    patch_signature  = Column(String(256), index=True) # e.g. "module:strategy"
    subsystem        = Column(String(128), index=True)
    outcome          = Column(String(32), index=True) # success | failure
    failure_reason   = Column(Text)
    verifier_rejections = Column(SmartJSON(), default=list)
    score            = Column(Float, default=0.0)
    recurrence_within_window = Column(Integer, default=0)
    recorded_at      = Column(DateTime(timezone=True), default=_utcnow)


class RepairPattern(Base):
    __tablename__ = "repair_patterns"

    id             = Column(GUID, primary_key=True, default=uuid.uuid4)
    pattern_id     = Column(String(64), unique=True, nullable=False, index=True)
    subsystem      = Column(String(128), index=True)
    strategy       = Column(String(32))
    success_rate   = Column(Float, default=0.0)
    failure_count  = Column(Integer, default=0)
    avg_risk       = Column(Float, default=0.0)
    last_detected_at = Column(DateTime(timezone=True), default=_utcnow)


class SelfTuningSuggestion(Base):
    __tablename__ = "self_tuning_suggestions"

    id              = Column(GUID, primary_key=True, default=uuid.uuid4)
    suggestion_id   = Column(String(64), unique=True, nullable=False, index=True)
    parameter_name  = Column(String(64), nullable=False)
    current_value   = Column(Float, nullable=False)
    proposed_value  = Column(Float, nullable=False)
    reason          = Column(Text, nullable=False)
    expected_impact = Column(Text)
    status          = Column(String(32), default="pending") # pending | applied | rejected
    created_at      = Column(DateTime(timezone=True), default=_utcnow)


# ── Phase 32: UI Repair & PR Governance ──────────────────

class UIRepairPRReview(Base):
    __tablename__ = "repair_ui_pr_reviews"

    id              = Column(GUID, primary_key=True, default=uuid.uuid4)
    review_id       = Column(String(64), unique=True, nullable=False, index=True)
    case_id         = Column(String(64), nullable=False, index=True) # Linked to RepairJobRecord.job_id
    pr_url          = Column(String(512), nullable=False)
    status          = Column(String(32), nullable=False, index=True)
    # PENDING | RUNNING | PASSED | CHANGES_REQUESTED | BLOCKED | FAILED | MANUAL_REVIEW_REQUIRED
    summary         = Column(Text, default="")
    confidence_score = Column(Float, default=0.0)
    verifier_mesh_pass = Column(Boolean, default=False)
    governance_decision = Column(String(32), default="PENDING")
    created_at      = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at      = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class UIRepairPRFinding(Base):
    __tablename__ = "ui_repair_pr_findings"

    id              = Column(GUID, primary_key=True, default=uuid.uuid4)
    finding_id      = Column(String(64), unique=True, nullable=False, index=True)
    review_id       = Column(String(64), nullable=False, index=True)
    file_path       = Column(String(512), nullable=True)
    line_number     = Column(Integer, nullable=True)
    severity        = Column(String(16), nullable=False) # info | warning | error | critical
    category        = Column(String(64), nullable=False) # security | quality | logic | style
    message         = Column(Text, nullable=False)
    suggestion      = Column(Text, nullable=True)
    created_at      = Column(DateTime(timezone=True), default=_utcnow, nullable=False)


# ── Phase 32B: External Agent Capability Registry & Sandbox ──

class AgentCapabilityModel(Base):
    __tablename__ = "repair_agent_capabilities"

    id                       = Column(GUID, primary_key=True, default=uuid.uuid4)
    agent_key                = Column(String(64), unique=True, nullable=False, index=True)
    agent_name               = Column(String(128), nullable=False)
    description              = Column(Text, default="")
    enabled                  = Column(Boolean, default=False, nullable=False)
    risk_level               = Column(String(32), default="medium", nullable=False) # low|medium|high|critical
    allowed_directories      = Column(SmartJSON(), default=list)
    blocked_directories      = Column(SmartJSON(), default=list)
    allowed_commands         = Column(SmartJSON(), default=list)
    blocked_commands         = Column(SmartJSON(), default=list)
    sandbox_mode             = Column(String(32), default="read-only", nullable=False) # read-only|workspace-write|full-sandbox
    max_cost_limit           = Column(Float, default=10.0, nullable=False)
    requires_human_approval = Column(Boolean, default=True, nullable=False)
    network_policy           = Column(String(32), default="disabled", nullable=False) # disabled|restricted|allowed
    allowed_domains          = Column(SmartJSON(), default=list)
    created_at               = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at               = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)


class AgentRunModel(Base):
    __tablename__ = "repair_agent_runs"

    id                = Column(GUID, primary_key=True, default=uuid.uuid4)
    run_id            = Column(String(64), unique=True, nullable=False, index=True)
    agent_key         = Column(String(64), nullable=False, index=True)
    status            = Column(String(32), default="PENDING", nullable=False) # PENDING|RUNNING|COMPLETED|FAILED|BLOCKED
    workspace_path    = Column(String(512), nullable=True)
    input_parameters  = Column(SmartJSON(), default=dict)
    commands_executed = Column(SmartJSON(), default=list)
    policy_violations = Column(SmartJSON(), default=list)
    exit_code         = Column(Integer, nullable=True)
    stdout            = Column(Text, default="")
    stderr            = Column(Text, default="")
    cost              = Column(Float, default=0.0, nullable=False)
    started_at        = Column(DateTime(timezone=True), nullable=True)
    completed_at      = Column(DateTime(timezone=True), nullable=True)
    timeout_seconds   = Column(Integer, default=300, nullable=False)
    sandbox_mode      = Column(String(32), nullable=False)
    network_policy    = Column(String(32), nullable=False)
    input_hash        = Column(String(128), nullable=True)
    command_hash      = Column(String(128), nullable=True)
    output_hash       = Column(String(128), nullable=True)
    workspace_hash    = Column(String(128), nullable=True)
    ledger_chain_id   = Column(String(128), nullable=True, index=True)
    created_by        = Column(String(64), nullable=True)
    created_at        = Column(DateTime(timezone=True), default=_utcnow, nullable=False)


class AgentArtifactPromotionModel(Base):
    __tablename__ = "repair_agent_promotions"

    id                     = Column(GUID, primary_key=True, default=uuid.uuid4)
    promotion_id           = Column(String(64), unique=True, nullable=False, index=True)
    run_id                 = Column(String(64), nullable=False, index=True)
    artifact_type          = Column(String(32), nullable=False) # patch | source_file | test_file
    sandbox_artifact_path  = Column(String(512), nullable=False)
    target_repo_path       = Column(String(512), nullable=False)
    artifact_hash          = Column(String(128), nullable=False)
    manifest_hash          = Column(String(128), nullable=True)
    verified_artifact_hash = Column(String(128), nullable=True)
    approved_artifact_hash = Column(String(128), nullable=True)
    promoted_artifact_hash = Column(String(128), nullable=True)
    target_path_hash       = Column(String(128), nullable=True)
    status                 = Column(String(32), default="PENDING_VERIFICATION", nullable=False, index=True)
    verification_score     = Column(Float, default=0.0, nullable=False)
    verification_details   = Column(SmartJSON(), default=dict)
    approved_by            = Column(String(128), nullable=True)
    approved_at            = Column(DateTime(timezone=True), nullable=True)
    promoted_at            = Column(DateTime(timezone=True), nullable=True)
    ledger_event_hash      = Column(String(128), nullable=True, index=True)
    created_at             = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

