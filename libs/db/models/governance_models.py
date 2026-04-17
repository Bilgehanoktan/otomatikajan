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
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from libs.db.base import Base, SmartJSON, utcnow

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

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    component_name = Column(String(100), nullable=False, index=True)
    version        = Column(String(50), nullable=False)
    status         = Column(SAEnum(SignoffStatus), default=SignoffStatus.PENDING, nullable=False)
    
    approver_id    = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approver_note  = Column(Text, nullable=True)
    
    evidence_summary = Column(SmartJSON(), nullable=True) # Test ID'leri, rapor linkleri
    policy_hash      = Column(String(64), nullable=True)  # Onay anındaki yönetişim politikası özeti
    
    created_at     = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at     = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Approver user ile ilişki (Opsiyonel, sistem otonom onay da verebilir)
    approver = relationship("User", foreign_keys=[approver_id])

class ValidationResult(Base):
    """
    Doğrulama Fabrikası (Proof Engine) Sonuçları.
    Sistemin anayasal kurallara ve regresyon testlerine uyum geçmişi.
    """
    __tablename__ = "validation_results"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    component_name = Column(String(100), nullable=False, index=True)
    test_suite     = Column(String(100), nullable=False) # e.g. "SecurityMesh", "EconomicAudit"
    
    validation_type= Column(SAEnum(ValidationType), nullable=False)
    status         = Column(SAEnum(ValidationStatus), nullable=False)
    
    metrics        = Column(SmartJSON(), nullable=True) # {regression_score: 0.98, cost_variance: 0.02...}
    raw_logs       = Column(Text, nullable=True)
    
    signoff_id     = Column(UUID(as_uuid=True), ForeignKey("production_signoffs.id"), nullable=True)
    
    created_at     = Column(DateTime(timezone=True), default=utcnow, nullable=False)

class HandoverEvent(Base):
    """
    Sorumluluk ve Yetki Devri Kayıtları (R-12).
    İnsan -> Makine veya Takım A -> Takım B sorumluluk geçişleri.
    """
    __tablename__ = "handover_events"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    signoff_id = Column(UUID(as_uuid=True), ForeignKey("production_signoffs.id"), nullable=True)
    proposal_id = Column(UUID(as_uuid=True), ForeignKey("policy_proposals.id"), nullable=True)
    
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

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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
