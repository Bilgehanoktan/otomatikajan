"""
Sovereign AGI — Phase 32: SIF-01 (Sovereign Identity Framework)
Identity and Access Management Models.
Supports RBAC + Granular Permissions + Scoping + System Identities.
"""

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer,
    String, Text, Enum as SAEnum, Table
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from libs.db.base import Base, utcnow, GUID


class Operator(Base):
    """
    Human operators with defined institutional roles.
    Replaces/extends the basic User model for corporate governance.
    """
    __tablename__ = "operators"
    __table_args__ = {"extend_existing": True}

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # High-level profile
    role = Column(String(50), nullable=False, default="AUDIT_OBSERVER")
    
    is_active = Column(Boolean, default=True)
    department = Column(String(100), nullable=True) # e.g., 'security', 'finance'
    region = Column(String(100), nullable=True)     # e.g., 'US-EAST', 'EU-CENTRAL'
    
    created_at = Column(DateTime(timezone=True), default=utcnow)
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    permissions = relationship("PermissionGrant", back_populates="operator", cascade="all, delete-orphan")


class SystemIdentity(Base):
    """
    Autonomous agents, background workers, and external services.
    Enables tracking of non-human initiated actions.
    """
    __tablename__ = "system_identities"
    __table_args__ = {"extend_existing": True}

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False)
    identity_type = Column(String(50), nullable=False) # 'agent', 'worker', 'service', 'cron'
    
    # System roles define baseline capabilities for the agent
    role = Column(String(50), nullable=False, default="AUTONOMOUS_AGENT")
    
    is_active = Column(Boolean, default=True)
    api_key_hash = Column(String(128), unique=True, nullable=True) # For secure service-to-service auth
    # SIF-03: Lifecycle Telemetry
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    key_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # SIF-04: Risk & Trust Metrics
    trust_score = Column(Integer, default=100) # 0-100
    risk_level = Column(String(20), default="LOW") # LOW, MEDIUM, HIGH, CRITICAL
    quarantined_at = Column(DateTime(timezone=True), nullable=True)
    risk_reason = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), default=utcnow)

    # Relationships
    permissions = relationship("PermissionGrant", back_populates="system_identity", cascade="all, delete-orphan")


class PermissionGrant(Base):
    """
    The Core Matrix: Defines who can do what and in which scope.
    Pattern: [Identity] can [Permission] in [Scope] with [Effect].
    """
    __tablename__ = "permission_grants"
    __table_args__ = {"extend_existing": True}

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    
    # Subject (Either Operator or SystemIdentity)
    operator_id = Column(GUID, ForeignKey("operators.id", ondelete="CASCADE"), nullable=True)
    system_id = Column(GUID, ForeignKey("system_identities.id", ondelete="CASCADE"), nullable=True)
    
    # Action (e.g., 'workflow.execute', 'policy.approve')
    permission = Column(String(100), nullable=False, index=True)
    
    # Scope (Where the permission applies)
    # Types: 'global', 'region', 'project', 'department'
    scope_type = Column(String(50), nullable=False, default="global")
    # Value: region name, project_id, etc. NULL means matches everything in type.
    scope_value = Column(String(255), nullable=True)
    
    # Result
    effect = Column(String(10), nullable=False, default="allow") # 'allow' or 'deny'
    
    created_at = Column(DateTime(timezone=True), default=utcnow)
    granted_by = Column(GUID, nullable=True) # ID of the Prime who granted this

    # Reverse relations
    operator = relationship("Operator", back_populates="permissions")
    system_identity = relationship("SystemIdentity", back_populates="permissions")

class RefreshToken(Base):
    """
    Session persistence layer.
    Enables revokable long-term sessions for human operators.
    """
    __tablename__ = "refresh_tokens"
    __table_args__ = {"extend_existing": True}

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("operators.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(512), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

class PermissionAudit(Base):
    """SIF-03: Tracks all changes to the permission matrix."""
    __tablename__ = "permission_audits"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    actor_id = Column(GUID, nullable=False) # The PRIME operator making the change
    target_id = Column(GUID, nullable=False) # The operator/system receiving the change
    action = Column(String(50), nullable=False) # 'GRANT' or 'REVOKE'
    permission = Column(String(100), nullable=False)
    scope = Column(String(255), nullable=True)
    justification = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
