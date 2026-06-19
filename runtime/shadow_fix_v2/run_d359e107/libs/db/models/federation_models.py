"""
Sovereign AGI — Phase 19
libs/db/models/federation_models.py
Database models for Global Orchestration, Agent Federation, and Arbitration.
"""
from __future__ import annotations

import enum
import uuid

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy import Enum as SAEnum

from libs.db.base import GUID
from libs.db.models.core_models import Base, SmartJSON, utcnow


class FederatedActionType(str, enum.Enum):
    ROUTING = "ROUTING"
    ARBITRATION = "ARBITRATION"
    CONSENSUS = "CONSENSUS"
    QUARANTINE = "QUARANTINE"
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"

class FederationEvent(Base):
    """Audit trail for global federation decisions and cluster interactions."""
    __tablename__ = "federation_events"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    project_id = Column(GUID, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    event_type = Column(SAEnum(FederatedActionType), nullable=False, index=True)

    primary_cluster_id = Column(String(100), nullable=True, index=True)
    affected_clusters = Column(SmartJSON(), nullable=True) # List of cluster IDs involved

    action_summary = Column(String(500), nullable=False)
    payload = Column(SmartJSON(), nullable=True) # Detailed info (arbitration results, costs)

    confidence_score = Column(Float, default=1.0)
    was_successful = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

class AgentClusterMetric(Base):
    """Performance metrics per agent cluster for trust and efficiency scoring."""
    __tablename__ = "agent_cluster_metrics"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    cluster_id = Column(String(100), nullable=False, index=True, unique=True)

    trust_score = Column(Float, default=0.8) # 0.0 - 1.0 baseline
    total_proposals = Column(Integer, default=0)
    successful_proposals = Column(Integer, default=0)
    rolled_back_proposals = Column(Integer, default=0)

    total_tokens_used = Column(Integer, default=0)
    total_cost_usd = Column(Float, default=0.0)

    last_active_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
