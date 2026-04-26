"""
Sovereign AGI Yönetişim ve Anayasal Uyum Modelleri — Faz 29
Üretim onayı (Sign-off), Kesintisiz Doğrulama (Continuous Validation)
ve Sorumluluk Devri (Handover) süreçlerinin kalıcı kaydı.
"""

import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, DateTime, String, Text, ForeignKey, Integer, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from libs.db.base import Base, SmartJSON, utcnow, GUID

class SignoffStatus(str, enum.Enum):
    PENDING = "PENDING"
    SIGNED = "SIGNED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"

class ValidationType(str, enum.Enum):
    CONTINUOUS = "CONTINUOUS" # Periyodik sağlık taraması
    MANUAL = "MANUAL"         # Manuel tetiklenen test
    DRILL = "DRILL"           # Simülasyon/Tatbikat (Game Day)
    PRE_DEPLOY = "PRE_DEPLOY" # Dağıtım öncesi son kontrol

class ValidationStatus(str, enum.Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"
    SKIPPED = "SKIPPED"

class ProductionSignoff(Base):
    """
    Üretim Ortamı Onay Sicili.
    Her kritik bileşenin (Repair, Orchestrator, Auth) üretim durumu burada tescillenir.
    """
    __tablename__ = "production_signoffs"
    __table_args__ = {"extend_existing": True}

    id             = Column(GUID, primary_key=True, default=uuid.uuid4)
    component_name = Column(String(100), nullable=False, index=True)
    version        = Column(String(50), nullable=False)
    status         = Column(SAEnum(SignoffStatus), default=SignoffStatus.PENDING, nullable=False)
    
    approver_id    = Column(GUID, ForeignKey("operators.id"), nullable=True)
    approver_note  = Column(Text, nullable=True)
    
    evidence_summary = Column(SmartJSON(), nullable=True) # Test ID'leri, rapor linkleri
    policy_hash      = Column(String(64), nullable=True)  # Onay anındaki yönetişim politikası özeti
    
    created_at     = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at     = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Approver operator ile ilişki (Opsiyonel, sistem otonom onay da verebilir)
    approver = relationship("Operator", foreign_keys=[approver_id])

class ValidationResult(Base):
    """
    Doğrulama Fabrikası (Proof Engine) Sonuçları.
    Sistemin anayasal kurallara ve regresyon testlerine uyum geçmişi.
    """
    __tablename__ = "validation_results"

    id             = Column(GUID, primary_key=True, default=uuid.uuid4)
    component_name = Column(String(100), nullable=False, index=True)
    test_suite     = Column(String(100), nullable=False) # e.g. "SecurityMesh", "EconomicAudit"
    
    validation_type= Column(SAEnum(ValidationType), nullable=False)
    status         = Column(SAEnum(ValidationStatus), nullable=False)
    
    metrics        = Column(SmartJSON(), nullable=True) # {regression_score: 0.98, cost_variance: 0.02...}
    raw_logs       = Column(Text, nullable=True)
    
    signoff_id     = Column(GUID, ForeignKey("production_signoffs.id"), nullable=True)
    
    created_at     = Column(DateTime(timezone=True), default=utcnow, nullable=False)

class HandoverEvent(Base):
    """
    Sorumluluk ve Yetki Devri Kayıtları (R-12).
    İnsan -> Makine veya Takım A -> Takım B sorumluluk geçişleri.
    """
    __tablename__ = "handover_events"

    id             = Column(GUID, primary_key=True, default=uuid.uuid4)
    asset_id       = Column(String(100), nullable=False, index=True) # e.g. "fleet_101", "budget_api"
    
    source_owner   = Column(String(100), nullable=False) # "SystemManager", "AutonomousGuard"
    target_owner   = Column(String(100), nullable=False)
    
    context        = Column(SmartJSON(), nullable=True) # Devir anındaki sistem durumu
    justification  = Column(Text, nullable=True)
    
    timestamp      = Column(DateTime(timezone=True), default=utcnow, nullable=False)

class QuorumRequirement(Base):
    """
    Onay Matrisi (Policy-Driven Quorum).
    BileÅen tipi ve risk seviyesine gÃ¶re gereken onay sayÄ±sÄ±nÄ± belirler.
    """
    __tablename__ = "signoff_quorum_requirements"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    component_type = Column(String(100), nullable=False) # "REPAIR", "SCALING", "SECURITY", "CONSTITUTION"
    risk_level = Column(String(50), default="LOW")  # LOW, MEDIUM, HIGH, CRITICAL
    
    required_quorum = Column(Integer, default=1)
    description = Column(String(255), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=utcnow)

class MultiPartySignoff(Base):
    """
    Birden fazla operatÃ¶rÃ¼n (vaya otonom muhafÄ±zÄ±n) onay/ret kaydÄ±nÄ± tutar.
    """
    __tablename__ = "multi_party_signoffs"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    signoff_id = Column(GUID, ForeignKey("production_signoffs.id"), nullable=True)
    proposal_id = Column(GUID, ForeignKey("policy_proposals.id"), nullable=True)
    
    approver_id = Column(String(100), nullable=False) # User or Agent ID
    status = Column(SAEnum(SignoffStatus), default=SignoffStatus.SIGNED)
    
    note = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=utcnow)

class PolicyProposal(Base):
    """
    YÃ¶netiÅÅŸim anayasasÄ± (Constitution) iÃ§in UI Ã¼zerinden gelen teklifleri tutar.
    Kabul edildiÄinde Git mÃ¼hÃ¼rleme sÃ¼recini tetikler.
    """
    __tablename__ = "policy_proposals"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    scope = Column(String(50), default="GLOBAL") # GLOBAL, FINANCE, SECURITY, OPS
    proposed_changes = Column(SmartJSON(), nullable=False) # Git patch or JSON structure
    
    status = Column(String(50), default="PROPOSED") # PROPOSED, APPROVED, REJECTED, COMMITTED
    author_id = Column(String(100), nullable=False)
    
    # Git integration trace
    git_commit_sha = Column(String(64), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=utcnow)
    expires_at = Column(DateTime(timezone=True), nullable=True)


# ── Soft CEO Governor Tables ──────────────────────────────────

class GovernorCaseRecord(Base):
    """
    Governor tarama sonucu üretilen case snapshot'ı.
    Her taranan workflow için risk, karar ve bağlam bilgisi tutulur.
    """
    __tablename__ = "governor_cases"

    id                    = Column(GUID, primary_key=True, default=uuid.uuid4)
    project_id            = Column(GUID, nullable=False, index=True)
    project_title         = Column(String(500), default="")
    project_status        = Column(String(32), default="")

    pending_reason        = Column(String(32), nullable=False, index=True)
    risk_class            = Column(String(16), nullable=False, index=True)
    risk_score            = Column(Integer, default=0)  # 0-1000 (score * 1000)
    recommended_decision  = Column(String(64), nullable=False, index=True)
    decision_reason_codes = Column(SmartJSON(), default=list)

    # Durum bayrakları
    has_open_incident      = Column(Integer, default=0)
    has_safety_lock        = Column(Integer, default=0)
    has_active_fingerprint = Column(Integer, default=0)
    requires_prime         = Column(Integer, default=0)
    requires_quorum        = Column(Integer, default=0)
    missing_context        = Column(Integer, default=0)

    stale_seconds          = Column(Integer, default=0)
    snapshot_payload       = Column(SmartJSON(), default=dict)

    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class GovernorActionRecord(Base):
    """Governor'ın gerçekten uyguladığı aksiyonların kaydı."""
    __tablename__ = "governor_actions"

    id            = Column(GUID, primary_key=True, default=uuid.uuid4)
    case_id       = Column(GUID, nullable=True, index=True)
    project_id    = Column(GUID, nullable=False, index=True)
    action_type   = Column(String(64), nullable=False, index=True)
    status        = Column(String(32), default="executed")  # executed, failed, skipped
    executed_by   = Column(String(64), default="SOFT_CEO")  # SOFT_CEO, SOVEREIGN_PRIME, HUMAN_OPERATOR
    result_payload = Column(SmartJSON(), default=dict)
    created_at    = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)


class GovernorEscalationRecord(Base):
    """Prime/quorum/human context'e giden eskalasyonlar."""
    __tablename__ = "governor_escalations"

    id              = Column(GUID, primary_key=True, default=uuid.uuid4)
    case_id         = Column(GUID, nullable=True, index=True)
    project_id      = Column(GUID, nullable=False, index=True)
    escalation_type = Column(String(64), nullable=False)  # REQUIRES_PRIME_REVIEW, REQUIRES_QUORUM, REQUIRES_HUMAN_CONTEXT
    target_role     = Column(String(64), default="SOVEREIGN_PRIME")
    reason          = Column(Text, default="")
    status          = Column(String(32), default="open", index=True)  # open, resolved, dismissed
    created_at      = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    resolved_at     = Column(DateTime(timezone=True), nullable=True)

