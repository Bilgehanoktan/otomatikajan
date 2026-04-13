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
