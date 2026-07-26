"""
Sovereign AGI — Phase 31
libs/db/models/learning_models.py
Models for the Learning Engine (Self-Correction & Strategy Memory).
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer, String

from bilgeapi.libs.db.base import GUID, Base


class ErrorFingerprint(Base):
    """Aynı sınıf hataları gruplayan kimlik (Error Deduplication & Fingerprinting)."""
    __tablename__ = "error_fingerprints"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    fingerprint_hash = Column(String(64), unique=True, index=True) # Computed hash of family/component/signature

    error_family = Column(String, nullable=False) # e.g. "DATABASE_LOCK", "API_TIMEOUT"
    service = Column(String, nullable=False)      # e.g. "workflow_api"
    component = Column(String, nullable=False)    # e.g. "GovernanceRouter"

    exception_type = Column(String)               # e.g. "OperationalError"
    normalized_message = Column(String)           # Masked PII/Dynamic IDs
    stack_signature = Column(String)              # Hash of top 5 relevant stack frames

    severity = Column(String, default="medium")
    risk_domain = Column(String)                  # e.g. "persistence", "concurrency"

    first_seen_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    last_seen_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    recurrence_count = Column(Integer, default=1)

    is_active = Column(Boolean, default=True)
    integrity_hash = Column(String(64))           # Sealed integrity check
    meta_data = Column(JSON, default=dict)

class LearningRecord(Base):
    """Her incident / repair sonrası öğrenme kaydı (Post-Mortem Evidence)."""
    __tablename__ = "learning_records"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    fingerprint_id = Column(GUID, ForeignKey("error_fingerprints.id"), nullable=True)
    incident_id = Column(GUID, index=True)
    workflow_id = Column(GUID, nullable=True)
    project_id = Column(GUID, nullable=True)
    approval_id = Column(GUID, nullable=True)
    lineage_id = Column(GUID, nullable=True)

    root_cause = Column(String)
    proposed_fix_type = Column(String) # code, config, policy, data, infra, manual_override

    strategy_used = Column(String)
    verification_score = Column(Float)
    canary_result = Column(String)

    final_outcome = Column(String) # SUCCESS, FAILED, PARTIAL
    rollback_required = Column(Boolean, default=False)
    operator_override = Column(Boolean, default=False)

    repair_latency_s = Column(Float)
    cost_usd = Column(Float, default=0.0)
    confidence_after_resolution = Column(Float)

    applied_patch = Column(String, nullable=True) # The actual diff

    integrity_hash = Column(String(64))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

class StrategyMemory(Base):
    """Hangi çözüm tipi hangi durumda işe yarıyor? (Reinforcement Learning Signal)."""
    __tablename__ = "strategy_memory"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    component = Column(String, index=True)
    error_family = Column(String, index=True)
    strategy_name = Column(String, index=True)

    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    wrong_patch_count = Column(Integer, default=0)
    rollback_count = Column(Integer, default=0)
    operator_reject_count = Column(Integer, default=0)

    avg_repair_latency = Column(Float, default=0.0)
    avg_verification_score = Column(Float, default=0.0)
    avg_cost_usd = Column(Float, default=0.0)

    last_success_at = Column(DateTime(timezone=True), nullable=True)
    last_failure_at = Column(DateTime(timezone=True), nullable=True)

    trust_score = Column(Float, default=0.0)
    state = Column(String, default="observed") # observed, candidate, trusted, promoted, deprecated

    meta_data = Column(JSON, default=dict)

class NegativePatternMemory(Base):
    """Başarısız tamirlerden ve tehlikeli davranışlardan öğrenmek (Negative Constraints)."""
    __tablename__ = "negative_pattern_memory"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    fingerprint_id = Column(GUID, ForeignKey("error_fingerprints.id"), nullable=True)
    component = Column(String, index=True)
    strategy_name = Column(String, index=True)

    failure_reason = Column(String)
    rollback_reason = Column(String)
    blast_radius = Column(String) # low, medium, high

    penalty_weight = Column(Float, default=1.0)
    occurrence_count = Column(Integer, default=1)

    last_seen_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    meta_data = Column(JSON, default=dict)
