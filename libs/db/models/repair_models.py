"""
Repair DB Modelleri — Self-Repair sisteminin kalıcı depolaması.

Tablolar:
- repair_incidents   : normalize edilmiş olay kayıtları
- repair_jobs        : pipeline durum makinesi
- repair_proposals   : PR önerileri (onay bekleniyor)
- repair_patch_log   : geçmiş patch sonuçları (hafıza)
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, Float, Integer,
    String, Text, Index,
)
from sqlalchemy.dialects.postgresql import UUID
from libs.db.models import Base, SmartJSON


def _utcnow():
    return datetime.now(timezone.utc)


# ── Incident Kaydı ────────────────────────────────────────
class RepairIncident(Base):
    __tablename__ = "repair_incidents"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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

    id                  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    result_id     = Column(String(64), unique=True, nullable=False, index=True)
    candidate_id  = Column(String(64), nullable=False, index=True)
    verifier_name = Column(String(64), nullable=False) # build | regression | economic etc
    score         = Column(Float, default=0.0)
    passed        = Column(Boolean, default=False)
    details       = Column(SmartJSON(), default=dict) # breakdown details
    timestamp     = Column(DateTime(timezone=True), default=_utcnow)


class RepairMemory(Base):
    __tablename__ = "repair_memories"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pattern_id     = Column(String(64), unique=True, nullable=False, index=True)
    subsystem      = Column(String(128), index=True)
    strategy       = Column(String(32))
    success_rate   = Column(Float, default=0.0)
    failure_count  = Column(Integer, default=0)
    avg_risk       = Column(Float, default=0.0)
    last_detected_at = Column(DateTime(timezone=True), default=_utcnow)


class SelfTuningSuggestion(Base):
    __tablename__ = "self_tuning_suggestions"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    suggestion_id   = Column(String(64), unique=True, nullable=False, index=True)
    parameter_name  = Column(String(64), nullable=False)
    current_value   = Column(Float, nullable=False)
    proposed_value  = Column(Float, nullable=False)
    reason          = Column(Text, nullable=False)
    expected_impact = Column(Text)
    status          = Column(String(32), default="pending") # pending | applied | rejected
    created_at      = Column(DateTime(timezone=True), default=_utcnow)
