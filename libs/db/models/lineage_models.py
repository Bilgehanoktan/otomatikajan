"""
Sovereign AGI — Phase 29
libs/db/models/lineage_models.py
Models for tracking the lineage of autonomous decisions and policy evolutions.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy import Column, String, JSON, DateTime, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from libs.db.base import Base, GUID

class DecisionLineage(Base):
    """Otonom kararlarÄ±n soyaÄŸacÄ±nÄ± tutar (Decision Family Tree)."""
    __tablename__ = "decision_lineage"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    decision_type = Column(String, nullable=False) # e.g. "REPAIR", "POLICY_CHANGE", "SCALING"
    component_name = Column(String, nullable=False)
    
    # Parent decision (e.g. An anomaly detection that triggered this repair)
    parent_id = Column(GUID, ForeignKey("decision_lineage.id"), nullable=True)
    
    # Root trigger (The original event that started the chain)
    root_id = Column(GUID, nullable=True)
    
    trigger_event = Column(JSON, nullable=True) # The event data that triggered this
    summary = Column(String, nullable=True) # Short human-readable summary
    rationale = Column(String, nullable=True) # AI reasoning
    confidence_score = Column(Float, default=1.0)
    outcome = Column(String, nullable=True) # e.g. "APPROVED", "REJECTED", "SUCCESS"
    
    # Phase 30: Integrity check for institutional scale
    integrity_hash = Column(String(64), nullable=True, index=True)
    
    meta_data = Column(JSON, default=dict) # Additional context
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class PolicyEvolution(Base):
    """YÃ¶netiÅÅŸim politikalarÄ±nÄ±n evrimini (sÃ¼rÃ¼mlerini) tutar."""
    __tablename__ = "policy_evolution"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    policy_key = Column(String, nullable=False) # e.g. "BUDGET_THRESHOLD", "AUTONOMY_LEVEL"
    version = Column(String, nullable=False)
    
    previous_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=False)
    
    change_reason = Column(String, nullable=True)
    author_id = Column(String, nullable=True) # Agent ID or Human ID
    
    # Link to the decision that caused this change
    decision_id = Column(GUID, ForeignKey("decision_lineage.id"), nullable=True)
    
    status = Column(String, default="ACTIVE") # ACTIVE, SUPERSEDED, PROPOSED
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
