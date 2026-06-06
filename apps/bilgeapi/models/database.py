import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Float, ForeignKey, Boolean, Integer
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


class ApiKeyModel(Base):
    __tablename__ = "bilgeapi_api_keys"

    id = Column(String(64), primary_key=True)
    key_hash = Column(String(64), nullable=False, unique=True, index=True)
    key_prefix = Column(String(16), nullable=False)
    key_fingerprint = Column(String(16), nullable=False)
    role = Column(String(32), nullable=False, index=True)
    description = Column(Text, nullable=True)
    tenant_id = Column(String(64), nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_by = Column(String(64), nullable=True)
    revoked_by = Column(String(64), nullable=True)
    revoke_reason = Column(Text, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    quota_daily = Column(Integer, nullable=True)
    quota_monthly = Column(Integer, nullable=True)


class ResearchRequestModel(Base):
    __tablename__ = "bilgeapi_research_requests"

    id = Column(String(64), primary_key=True)
    incident_id = Column(String(64), nullable=False, index=True)
    query = Column(String(256), nullable=False)
    status = Column(String(32), default="PENDING", nullable=False, index=True) # PENDING, RUNNING, COMPLETED, FAILED
    error_message = Column(Text, nullable=True)
    tenant_id = Column(String(64), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    evidences = relationship("ResearchEvidenceModel", back_populates="research", cascade="all, delete-orphan", lazy="selectin")
    proposals = relationship("ImprovementProposalModel", back_populates="research", cascade="all, delete-orphan", lazy="selectin")


class ResearchEvidenceModel(Base):
    __tablename__ = "bilgeapi_research_evidences"

    id = Column(String(64), primary_key=True)
    research_id = Column(String(64), ForeignKey("bilgeapi_research_requests.id"), nullable=False, index=True)
    source_url = Column(String(512), nullable=False)
    source_domain = Column(String(128), nullable=False, index=True)
    title = Column(String(256), nullable=True)
    snippet = Column(Text, nullable=True)
    raw_content_summary = Column(Text, nullable=True)
    content_hash = Column(String(64), nullable=False)
    trust_score = Column(Float, nullable=False)
    retrieved_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    research = relationship("ResearchRequestModel", back_populates="evidences")


class ImprovementProposalModel(Base):
    __tablename__ = "bilgeapi_improvement_proposals"

    id = Column(String(64), primary_key=True)
    research_id = Column(String(64), ForeignKey("bilgeapi_research_requests.id"), nullable=False, index=True)
    title = Column(String(256), nullable=False)
    rationale = Column(Text, nullable=False)
    patch_code = Column(Text, nullable=False)
    risk_analysis = Column(SmartJSON(), nullable=True)
    gate_status = Column(String(32), default="DRAFT", nullable=False, index=True) # DRAFT, GATE_RUNNING, GATE_PASSED, GATE_FAILED
    gate_score = Column(Float, nullable=True)
    approval_status = Column(String(32), default="REVIEW_REQUIRED", nullable=False, index=True) # REVIEW_REQUIRED, APPROVED, REJECTED
    approved_by = Column(String(64), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    ready_for_human_apply = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    research = relationship("ResearchRequestModel", back_populates="proposals")


class PrDraftModel(Base):
    __tablename__ = "bilgeapi_pr_drafts"

    id = Column(String(64), primary_key=True)
    proposal_id = Column(String(64), ForeignKey("bilgeapi_improvement_proposals.id"), nullable=False, index=True)
    provider = Column(String(32), nullable=False)
    status = Column(String(32), default="PENDING", nullable=False, index=True) # PENDING, COMPLETED, FAILED, BLOCKED
    github_pr_url = Column(String(512), nullable=True)
    branch_name = Column(String(256), nullable=True)
    title = Column(String(256), nullable=False)
    body = Column(Text, nullable=False)
    evidence_hash = Column(String(64), nullable=True)
    risk_level = Column(String(32), nullable=False) # LOW, MEDIUM, HIGH
    risk_flags = Column(SmartJSON(), nullable=True)
    created_by = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    proposal = relationship("ImprovementProposalModel")


class PrVerificationModel(Base):
    __tablename__ = "bilgeapi_pr_verifications"

    id = Column(String(64), primary_key=True)
    pr_draft_id = Column(String(64), ForeignKey("bilgeapi_pr_drafts.id"), nullable=False, index=True)
    proposal_id = Column(String(64), ForeignKey("bilgeapi_improvement_proposals.id"), nullable=False, index=True)
    status = Column(String(32), default="PENDING", nullable=False, index=True) # PENDING, REVIEW_READY, NEEDS_HUMAN_CAUTION, NEEDS_REVISION, BLOCKED
    review_score = Column(Float, nullable=False)
    review_decision = Column(String(32), nullable=False) # REVIEW_READY, NEEDS_HUMAN_CAUTION, NEEDS_REVISION, BLOCKED
    risk_level = Column(String(32), nullable=False) # LOW, MEDIUM, HIGH
    risk_flags = Column(SmartJSON(), nullable=True) # E.g., list of risky files affected
    affected_files = Column(SmartJSON(), nullable=True) # List of file paths
    mutation_detected = Column(Boolean, default=False, nullable=False)
    test_files_present = Column(Boolean, default=False, nullable=False)
    patch_size_lines = Column(Integer, default=0, nullable=False)
    test_plan = Column(SmartJSON(), nullable=True) # Generated test plan details
    rollback_plan = Column(Text, nullable=True) # Suggested rollback steps
    verification_report = Column(Text, nullable=True) # Markdown report content
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    pr_draft = relationship("PrDraftModel")
    proposal = relationship("ImprovementProposalModel")


