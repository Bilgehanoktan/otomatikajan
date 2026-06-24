import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Float, Integer, Boolean, JSON
from sqlalchemy.orm import DeclarativeBase

class WorkspaceBase(DeclarativeBase):
    """Dedicated SQLAlchemy Base for the portable workspace memory SQLite database."""
    pass

def utcnow():
    return datetime.now(timezone.utc)

class SystemModel(WorkspaceBase):
    __tablename__ = "workspace_systems"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    system_name = Column(String(128), nullable=False)
    project_type = Column(String(64), nullable=False)
    root_path = Column(String(512), nullable=False)
    health_score = Column(Float, nullable=False, default=0.0)
    scanned_at = Column(DateTime, default=utcnow, nullable=False)
    metadata_fields = Column("metadata", JSON, nullable=True)


class TaskModel(WorkspaceBase):
    __tablename__ = "workspace_tasks"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(64), nullable=True, index=True)
    system_id = Column(String(64), nullable=False, index=True)
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    agent_role = Column(String(64), nullable=False)
    action_type = Column(String(64), nullable=False)
    status = Column(String(32), default="PENDING", nullable=False, index=True)  # PENDING, RUNNING, COMPLETED, FAILED, BLOCKED
    risk_level = Column(String(32), default="LOW", nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    payload = Column(JSON, nullable=True)
    attempt_count = Column(Integer, default=0, nullable=False)
    max_attempts = Column(Integer, default=3, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class EventLogModel(WorkspaceBase):
    __tablename__ = "workspace_event_logs"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    system_id = Column(String(64), nullable=False, index=True)
    event_type = Column(String(128), nullable=False, index=True)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)


class AuditLogModel(WorkspaceBase):
    """Records what was done, who did it, what the target was, and what the result was."""
    __tablename__ = "workspace_audit_logs"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(64), nullable=True, index=True)
    event_type = Column(String(128), nullable=False, index=True)
    actor_id = Column(String(64), nullable=False)
    actor_type = Column(String(64), nullable=False)
    action = Column(String(128), nullable=False)
    target = Column(String(512), nullable=False)
    before_state = Column(JSON, nullable=True)
    after_state = Column(JSON, nullable=True)
    status = Column(String(32), nullable=False)  # ALLOWED, DENIED, APPROVAL_REQUIRED
    risk_level = Column(String(32), nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)


class DecisionModel(WorkspaceBase):
    """Records why an action was allowed, denied, or sent for approval."""
    __tablename__ = "workspace_decisions"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(64), nullable=True, index=True)
    task_id = Column(String(64), nullable=True, index=True)
    classification = Column(String(128), nullable=False)
    risk_score = Column(Float, nullable=False)
    risk_level = Column(String(32), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    eligibility = Column(String(64), nullable=False)
    requires_human_gate = Column(Boolean, default=False, nullable=False)
    decision_reason = Column(Text, nullable=False)
    reasons = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)


class ApprovalModel(WorkspaceBase):
    __tablename__ = "workspace_approvals"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(64), nullable=True, index=True)
    task_id = Column(String(64), nullable=False, index=True)
    decision_id = Column(String(64), nullable=False, index=True)
    request_type = Column(String(64), nullable=False)
    status = Column(String(32), default="PENDING", nullable=False, index=True)  # PENDING, APPROVED, REJECTED, EXPIRED, DENIED
    reason = Column(Text, nullable=True)
    token = Column(String(128), nullable=False)
    action_hash = Column(String(64), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    approved_by = Column(String(128), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)


class QuarantineItemModel(WorkspaceBase):
    __tablename__ = "workspace_quarantine_items"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(64), nullable=True, index=True)
    filepath = Column(String(512), nullable=False, index=True)
    original_hash = Column(String(64), nullable=False)
    quarantine_path = Column(String(512), nullable=False)
    reason = Column(Text, nullable=True)
    restored = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
