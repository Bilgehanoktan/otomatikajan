import sys
if __name__ == "apps.bilgeapi.models.database":
    sys.modules["bilgeapi.models.database"] = sys.modules[__name__]
elif __name__ == "bilgeapi.models.database":
    sys.modules["apps.bilgeapi.models.database"] = sys.modules[__name__]

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Float, ForeignKey, Boolean, Integer, UniqueConstraint
from sqlalchemy.orm import relationship
from libs.db.base import Base, SmartJSON

def utcnow():
    return datetime.now(timezone.utc)

class IncidentModel(Base):
    __tablename__ = "bilgeapi_incidents"
    __table_args__ = {"extend_existing": True}

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
    __table_args__ = {"extend_existing": True}

    diagnostic_id = Column(String(64), primary_key=True)
    incident_id = Column(String(64), nullable=False, index=True)
    status = Column(String(32), nullable=False, index=True)
    summary = Column(Text, nullable=True)
    root_cause_hypothesis = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    risk_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    findings = relationship(lambda: FindingModel, back_populates="diagnostic", cascade="all, delete-orphan", lazy="selectin")
    recommendations = relationship(lambda: RecommendationModel, back_populates="diagnostic", cascade="all, delete-orphan", lazy="selectin")


class FindingModel(Base):
    __tablename__ = "bilgeapi_findings"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True)
    diagnostic_id = Column(String(64), ForeignKey("bilgeapi_diagnostic_runs.diagnostic_id"), nullable=False, index=True)
    description = Column(Text, nullable=False)
    metadata_fields = Column("metadata", SmartJSON(), nullable=True)

    diagnostic = relationship(DiagnosticRunModel, back_populates="findings")


class RecommendationModel(Base):
    __tablename__ = "bilgeapi_recommendations"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True)
    diagnostic_id = Column(String(64), ForeignKey("bilgeapi_diagnostic_runs.diagnostic_id"), nullable=False, index=True)
    description = Column(Text, nullable=False)
    metadata_fields = Column("metadata", SmartJSON(), nullable=True)

    diagnostic = relationship(DiagnosticRunModel, back_populates="recommendations")


class RepairRequestModel(Base):
    __tablename__ = "bilgeapi_repair_requests"
    __table_args__ = {"extend_existing": True}

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
    __table_args__ = {"extend_existing": True}

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
    __table_args__ = {"extend_existing": True}

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
    __table_args__ = {"extend_existing": True}

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
    __table_args__ = {"extend_existing": True}

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


class ResearchEvidenceModel(Base):
    __tablename__ = "bilgeapi_research_evidences"
    __table_args__ = {"extend_existing": True}

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

    research = relationship(lambda: ResearchRequestModel, back_populates="evidences")


class ImprovementProposalModel(Base):
    __tablename__ = "bilgeapi_improvement_proposals"
    __table_args__ = {"extend_existing": True}

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

    research = relationship(lambda: ResearchRequestModel, back_populates="proposals")


class ResearchRequestModel(Base):
    __tablename__ = "bilgeapi_research_requests"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True)
    incident_id = Column(String(64), nullable=False, index=True)
    query = Column(String(256), nullable=False)
    status = Column(String(32), default="PENDING", nullable=False, index=True) # PENDING, RUNNING, COMPLETED, FAILED
    error_message = Column(Text, nullable=True)
    tenant_id = Column(String(64), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    evidences = relationship(lambda: ResearchEvidenceModel, back_populates="research", cascade="all, delete-orphan", lazy="selectin")
    proposals = relationship(lambda: ImprovementProposalModel, back_populates="research", cascade="all, delete-orphan", lazy="selectin")


class PrDraftModel(Base):
    __tablename__ = "bilgeapi_pr_drafts"
    __table_args__ = {"extend_existing": True}

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

    proposal = relationship(lambda: ImprovementProposalModel)


class PrVerificationModel(Base):
    __tablename__ = "bilgeapi_pr_verifications"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True)
    pr_draft_id = Column(String(64), ForeignKey("bilgeapi_pr_drafts.id"), nullable=False, index=True)
    proposal_id = Column(String(64), ForeignKey("bilgeapi_improvement_proposals.id"), nullable=False, index=True)
    revision_id = Column(String(64), ForeignKey("bilgeapi_patch_revisions.id"), nullable=True, index=True)
    ai_suggestion_id = Column(String(64), ForeignKey("bilgeapi_ai_patch_suggestions.id"), nullable=True, index=True)
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

    pr_draft = relationship(lambda: PrDraftModel)
    proposal = relationship(lambda: ImprovementProposalModel)
    revision = relationship(lambda: PatchRevisionModel)
    ai_suggestion = relationship(lambda: AIPatchSuggestionModel, foreign_keys=lambda: [PrVerificationModel.ai_suggestion_id])


class PrReviewFeedbackModel(Base):
    __tablename__ = "bilgeapi_pr_review_feedbacks"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True)
    pr_draft_id = Column(String(64), ForeignKey("bilgeapi_pr_drafts.id"), nullable=False, index=True)
    reviewer_id = Column(String(64), nullable=False)
    comment = Column(Text, nullable=False)
    status = Column(String(32), default="PENDING", nullable=False, index=True) # PENDING, RESOLVED, SUPERSEDED
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    pr_draft = relationship(lambda: PrDraftModel)


class PatchRevisionModel(Base):
    __tablename__ = "bilgeapi_patch_revisions"
    __table_args__ = (UniqueConstraint('pr_draft_id', 'revision_number', name='uq_pr_draft_revision'), {"extend_existing": True})

    id = Column(String(64), primary_key=True)
    pr_draft_id = Column(String(64), ForeignKey("bilgeapi_pr_drafts.id"), nullable=False, index=True)
    feedback_id = Column(String(64), ForeignKey("bilgeapi_pr_review_feedbacks.id"), nullable=True, index=True)
    revision_number = Column(Integer, nullable=False)
    revised_patch_code = Column(Text, nullable=False)
    risk_analysis = Column(SmartJSON(), nullable=True)
    risk_level = Column(String(32), default="LOW", nullable=False) # LOW, MEDIUM, HIGH
    verification_status = Column(String(32), default="PENDING", nullable=False, index=True) # PENDING, VERIFIED, FAILED
    created_by = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    pr_draft = relationship(lambda: PrDraftModel)
    feedback = relationship(lambda: PrReviewFeedbackModel)


class ReviewLedgerEntryModel(Base):
    __tablename__ = "bilgeapi_review_ledger_entries"
    __table_args__ = (UniqueConstraint("chain_id", "sequence_no", name="uq_review_ledger_chain_sequence"), {"extend_existing": True})

    id = Column(String(64), primary_key=True)
    chain_id = Column(String(128), nullable=False, index=True)
    sequence_no = Column(Integer, nullable=False)
    event_type = Column(String(64), nullable=False, index=True)
    entity_type = Column(String(64), nullable=False, index=True)
    entity_id = Column(String(64), nullable=False, index=True)
    actor_id = Column(String(64), nullable=True, index=True)
    previous_hash = Column(String(64), nullable=True)
    payload_hash = Column(String(64), nullable=False)
    event_hash = Column(String(64), nullable=False, unique=True, index=True)
    payload_summary = Column(SmartJSON(), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)


class AIPatchSuggestionModel(Base):
    __tablename__ = "bilgeapi_ai_patch_suggestions"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True)
    pr_draft_id = Column(String(64), ForeignKey("bilgeapi_pr_drafts.id"), nullable=False, index=True)
    feedback_id = Column(String(64), ForeignKey("bilgeapi_pr_review_feedbacks.id"), nullable=True, index=True)
    revision_id = Column(String(64), ForeignKey("bilgeapi_patch_revisions.id"), nullable=True, index=True)
    provider = Column(String(32), default="mock", nullable=False)
    model_name = Column(String(128), nullable=True)
    prompt_hash = Column(String(128), nullable=False, index=True)
    context_summary = Column(SmartJSON(), nullable=True)
    suggested_patch_code = Column(Text, nullable=False)
    rationale = Column(Text, nullable=True)
    risk_notes = Column(Text, nullable=True)
    risk_level = Column(String(32), default="LOW", nullable=False, index=True)
    verification_id = Column(String(64), ForeignKey("bilgeapi_pr_verifications.id"), nullable=True, index=True)
    status = Column(String(32), default="GENERATED", nullable=False, index=True)
    created_by = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    pr_draft = relationship(lambda: PrDraftModel)
    feedback = relationship(lambda: PrReviewFeedbackModel)
    revision = relationship(lambda: PatchRevisionModel)
    verification = relationship(lambda: PrVerificationModel, foreign_keys=lambda: [AIPatchSuggestionModel.verification_id])


class SystemFindingModel(Base):
    __tablename__ = "bilgeapi_system_findings"
    __table_args__ = (
        UniqueConstraint("source_hash", name="uq_bilgeapi_system_findings_source_hash"),
        {"extend_existing": True}
    )

    id = Column(String(64), primary_key=True)
    tenant_id = Column(String(64), nullable=True, index=True)
    source_type = Column(String(64), nullable=False, index=True)
    source_id = Column(String(128), nullable=False, index=True)
    source_hash = Column(String(64), nullable=False, unique=True, index=True)
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(32), nullable=False, index=True)
    risk_score = Column(Float, nullable=False)
    status = Column(String(32), default="OPEN", nullable=False, index=True)
    evidence_summary = Column(SmartJSON(), nullable=True)
    recommended_action = Column(Text, nullable=True)
    human_gate_payload = Column(SmartJSON(), nullable=True)
    occurrence_count = Column(Integer, default=1, nullable=False)
    first_seen_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    last_seen_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    acknowledged_by = Column(String(64), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    dismissed_by = Column(String(64), nullable=True)
    dismissed_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String(64), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    bilgeapi_research_id = Column(String(64), nullable=True, index=True)
    bilgeapi_proposal_id = Column(String(64), nullable=True, index=True)
    bilgeapi_pr_draft_id = Column(String(64), nullable=True, index=True)
    bilgeapi_verification_id = Column(String(64), nullable=True, index=True)
    bilgeapi_ledger_chain_id = Column(String(128), nullable=True, index=True)
    created_by = Column(String(64), nullable=True)
    correlation_id = Column(String(128), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class RemediationRunbookModel(Base):
    __tablename__ = "bilgeapi_remediation_runbooks"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=False, unique=True)
    action_type = Column(String(64), nullable=False)
    severity_allowed = Column(String(32), nullable=False)
    requires_human_gate = Column(Boolean, default=True, nullable=False)
    enabled = Column(Boolean, default=False, nullable=False)
    execution_mode = Column(String(32), default="MANUAL", nullable=False)
    max_attempts = Column(Integer, default=2, nullable=False)
    cooldown_seconds = Column(Integer, default=300, nullable=False)
    safety_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class RemediationAttemptModel(Base):
    __tablename__ = "bilgeapi_remediation_attempts"
    __table_args__ = {"extend_existing": True}

    id = Column(String(64), primary_key=True)
    finding_id = Column(String(64), ForeignKey("bilgeapi_system_findings.id"), nullable=False, index=True)
    runbook_id = Column(String(64), ForeignKey("bilgeapi_remediation_runbooks.id"), nullable=True, index=True)
    action_type = Column(String(64), nullable=False)
    status = Column(String(32), default="PENDING", nullable=False, index=True)
    attempt_no = Column(Integer, default=1, nullable=False)
    before_health = Column(SmartJSON(), nullable=True)
    after_health = Column(SmartJSON(), nullable=True)
    output_summary = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    policy_decision = Column(SmartJSON(), nullable=True)
    forbidden_actions_checked = Column(SmartJSON(), nullable=True)
    ledger_chain_id = Column(String(128), nullable=True, index=True)
    created_by = Column(String(64), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class BilgeAPIBridgeMappingModel(Base):
    __tablename__ = "bilgeapi_bridge_mappings"
    __table_args__ = (
        UniqueConstraint("source_type", "source_id", name="uq_bilgeapi_bridge_source"),
        {"extend_existing": True}
    )

    id = Column(String(64), primary_key=True)
    source_type = Column(String(64), nullable=False, index=True)
    source_id = Column(String(128), nullable=False, index=True)
    bilgeapi_finding_id = Column(String(64), nullable=True, index=True)
    bilgeapi_research_id = Column(String(64), nullable=True, index=True)
    bilgeapi_proposal_id = Column(String(64), nullable=True, index=True)
    bilgeapi_pr_draft_id = Column(String(64), nullable=True, index=True)
    bilgeapi_verification_id = Column(String(64), nullable=True, index=True)
    bilgeapi_ledger_chain_id = Column(String(128), nullable=True, index=True)
    status = Column(String(32), default="INIT", nullable=False, index=True)


class AgentTaskQueueModel(Base):
    __tablename__ = "bilgeapi_agent_task_queue"
    __table_args__ = {"extend_existing": True}

    task_id = Column(String(64), primary_key=True)
    source = Column(String(64), nullable=True)
    agent_role = Column(String(64), nullable=False, index=True)
    action_type = Column(String(64), nullable=False)
    payload = Column(SmartJSON(), nullable=True)
    risk_level = Column(String(32), default="low")
    priority_score = Column(Float, default=0.0, index=True)
    status = Column(String(32), default="PENDING", nullable=False, index=True)
    idempotency_key = Column(String(128), nullable=True, unique=True, index=True)
    attempt_count = Column(Integer, default=0, nullable=False)
    max_attempts = Column(Integer, default=3, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class AgentTaskLeaseModel(Base):
    __tablename__ = "bilgeapi_agent_task_leases"
    __table_args__ = {"extend_existing": True}

    task_id = Column(String(64), ForeignKey("bilgeapi_agent_task_queue.task_id"), primary_key=True)
    lease_owner = Column(String(128), nullable=False, index=True)
    lease_expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    acquired_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class AgentOrchestrationRunModel(Base):
    __tablename__ = "bilgeapi_agent_orchestration_runs"
    __table_args__ = {"extend_existing": True}

    run_id = Column(String(64), primary_key=True)
    task_id = Column(String(64), nullable=False, index=True)
    status = Column(String(32), nullable=False, index=True)
    execution_summary = Column(Text, nullable=True)
    evidence_ledger_hash = Column(String(128), nullable=True)
    started_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


