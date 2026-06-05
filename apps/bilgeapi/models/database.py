import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from libs.db.base import Base, SmartJSON

def utcnow():
    return datetime.now(timezone.utc)

class IncidentModel(Base):
    __tablename__ = "bilgeapi_incidents"

    id = Column(String(64), primary_key=True)
    project_key = Column(String(64), nullable=False, index=True)
    source_system = Column(String(64), nullable=False, index=True)
    environment = Column(String(64), nullable=False, index=True)
    kind = Column(String(64), nullable=False)
    severity = Column(String(32), nullable=False, index=True)
    error_message = Column(Text, nullable=False)
    stack_trace = Column(Text, nullable=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    correlation_id = Column(String(64), nullable=False, index=True)
    tags = Column(SmartJSON(), nullable=True)
    metadata_fields = Column("metadata", SmartJSON(), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)


class DiagnosticRunModel(Base):
    __tablename__ = "bilgeapi_diagnostic_runs"

    diagnostic_id = Column(String(64), primary_key=True)
    incident_id = Column(String(64), nullable=False, index=True)
    status = Column(String(32), nullable=False, index=True)
    summary = Column(Text, nullable=True)
    root_cause_hypothesis = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    risk_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    findings = relationship("FindingModel", back_populates="diagnostic", cascade="all, delete-orphan", lazy="selectin")
    recommendations = relationship("RecommendationModel", back_populates="diagnostic", cascade="all, delete-orphan", lazy="selectin")


class FindingModel(Base):
    __tablename__ = "bilgeapi_findings"

    id = Column(String(64), primary_key=True)
    diagnostic_id = Column(String(64), ForeignKey("bilgeapi_diagnostic_runs.diagnostic_id"), nullable=False, index=True)
    description = Column(Text, nullable=False)
    metadata_fields = Column("metadata", SmartJSON(), nullable=True)

    diagnostic = relationship("DiagnosticRunModel", back_populates="findings")


class RecommendationModel(Base):
    __tablename__ = "bilgeapi_recommendations"

    id = Column(String(64), primary_key=True)
    diagnostic_id = Column(String(64), ForeignKey("bilgeapi_diagnostic_runs.diagnostic_id"), nullable=False, index=True)
    description = Column(Text, nullable=False)
    metadata_fields = Column("metadata", SmartJSON(), nullable=True)

    diagnostic = relationship("DiagnosticRunModel", back_populates="recommendations")


class RepairRequestModel(Base):
    __tablename__ = "bilgeapi_repair_requests"

    id = Column(String(64), primary_key=True)
    diagnostic_id = Column(String(64), nullable=False, index=True)
    requested_by = Column(String(64), nullable=False)
    approved_by = Column(String(64), nullable=True)
    approval_status = Column(String(32), nullable=False, index=True)
    risk_score = Column(Float, nullable=False)
    risk_reason = Column(Text, nullable=False)
    dispatch_status = Column(String(32), nullable=False, index=True)
    external_reference = Column(String(64), nullable=True)
    approval_required = Column(Boolean, default=True, nullable=False)
    rejection_reason = Column(Text, nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class AuditEventModel(Base):
    __tablename__ = "bilgeapi_audit_events"

    id = Column(String(64), primary_key=True)
    event_type = Column(String(64), nullable=False, index=True)
    actor_id = Column(String(64), nullable=False)
    actor_type = Column(String(64), nullable=False)
    entity_type = Column(String(64), nullable=False)
    entity_id = Column(String(64), nullable=False, index=True)
    request_id = Column(String(64), nullable=True)
    correlation_id = Column(String(64), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(256), nullable=True)
    before_state = Column(SmartJSON(), nullable=True)
    after_state = Column(SmartJSON(), nullable=True)
    metadata_fields = Column("metadata", SmartJSON(), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)


class WebhookDeliveryModel(Base):
    __tablename__ = "bilgeapi_webhook_deliveries"

    id = Column(String(64), primary_key=True)
    repair_request_id = Column(String(64), nullable=False, index=True)
    webhook_url = Column(String(256), nullable=False)
    status_code = Column(Float, nullable=True)
    delivery_status = Column(String(32), nullable=False)
    error_message = Column(Text, nullable=True)
    payload_hash = Column(String(64), nullable=False)
    attempt_count = Column(Float, default=1.0)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)


class ReleaseCheckModel(Base):
    __tablename__ = "bilgeapi_release_checks"

    id = Column(String(64), primary_key=True)
    status = Column(String(32), nullable=False, index=True)  # PASSED, WARNING, BLOCKED
    score = Column(Float, nullable=False)
    blockers = Column(SmartJSON(), nullable=True)
    warnings = Column(SmartJSON(), nullable=True)
    checked_modules = Column(SmartJSON(), nullable=True)
    checked_endpoints = Column(SmartJSON(), nullable=True)
    smoke_trace = Column(SmartJSON(), nullable=True)
    app_version = Column(String(64), nullable=True)
    git_sha = Column(String(64), nullable=True)
    environment = Column(String(64), nullable=True)
    triggered_by = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
