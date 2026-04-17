"""
Sovereign AGI — Phase 30
libs/db/models/compliance_models.py
Models for institutional compliance, data retention, and evidence integrity.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy import Column, String, JSON, DateTime, ForeignKey, Integer, Boolean
from libs.db.base import Base, GUID

class RetentionPolicy(Base):
    """Veri saklama politikalarÄ±nÄ± tanÄ±mlar."""
    __tablename__ = "compliance_retention_policies"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    data_category = Column(String, unique=True, nullable=False) # e.g. "TELEMETRY", "DECISION_LINEAGE", "DRILL_LOGS"
    
    hot_retention_days = Column(Integer, default=90)
    warm_retention_days = Column(Integer, default=365)
    cold_retention_days = Column(Integer, default=1095) # 3 Years
    is_permanent = Column(Boolean, default=False)
    
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class AuditBundle(Base):
    """Denetim iÃ§in hazÄ±rlanmÄ±Å mÃ¼hÃ¼rlÃ¼ kanÄ±t paketleri."""
    __tablename__ = "compliance_audit_bundles"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    bundle_name = Column(String, nullable=False)
    purpose = Column(String, nullable=True) # e.g. "SOC2_2026_Q2", "INCIDENT_RECOVERY_PROOF"
    
    # Range of investigation
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    
    evidence_metadata = Column(JSON, nullable=False) # Hangi lineage ve signofflar dahil edildi
    integrity_hash = Column(String, nullable=False) # Paketin bÃ¼tÃ¼nlÃ¼k mÃ¼hrÃ¼
    
    created_by = Column(String, nullable=False) # Operator ID
    storage_path = Column(String, nullable=True) # Export edilen dosyanÄ±n konumu
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class EvidenceSeal(Base):
    """YÃ¼ksek deÄerli kayÄ±tlarÄ±n (lineage, signoff) doÄruluÄunu mÃ¼hÃ¼rler."""
    __tablename__ = "compliance_evidence_seals"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    target_table = Column(String, nullable=False) # e.g. "decision_lineage"
    target_id = Column(GUID, nullable=False)
    
    seal_signature = Column(String, nullable=False)
    signer_id = Column(String, nullable=False) # System or Operator
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
