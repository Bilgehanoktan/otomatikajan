"""
Sovereign AGI Yönetişim ve Anayasal Uyum Modelleri — Faz 29
Üretim onayı (Sign-off), Kesintisiz Doğrulama (Continuous Validation)
ve Sorumluluk Devri (Handover) süreçlerinin kalıcı kaydı.
"""

import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, DateTime, String, Text, ForeignKey, Integer, Float, Enum as SAEnum, BigInteger
)
from sqlalchemy.orm import relationship
from libs.db.base import Base, SmartJSON, utcnow, GUID

class SignoffStatus(str, enum.Enum):
    PENDING = "PENDING"
    SIGNED = "SIGNED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"

class ValidationType(str, enum.Enum):
    CONTINUOUS = "CONTINUOUS"
    MANUAL = "MANUAL"
    DRILL = "DRILL"
    PRE_DEPLOY = "PRE_DEPLOY"

class ValidationStatus(str, enum.Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"
    SKIPPED = "SKIPPED"

class ProductionSignoff(Base):
    __tablename__ = "production_signoffs"
    __table_args__ = {"extend_existing": True}
    id             = Column(GUID, primary_key=True, default=uuid.uuid4)
    component_name = Column(String(100), nullable=False, index=True)
    version        = Column(String(50), nullable=False)
    status         = Column(SAEnum(SignoffStatus, native_enum=False), default=SignoffStatus.PENDING, nullable=False)
    approver_id    = Column(GUID, ForeignKey("operators.id"), nullable=True)
    approver_note  = Column(Text, nullable=True)
    evidence_summary = Column(SmartJSON(), nullable=True)

class ValidationResult(Base):
    __tablename__ = "validation_results"
    __table_args__ = {"extend_existing": True}
    id             = Column(GUID, primary_key=True, default=uuid.uuid4)
    component_name = Column(String(100), nullable=False, index=True)
    test_suite     = Column(String(100), nullable=True)
    validation_type = Column(SAEnum(ValidationType, native_enum=False), nullable=False)
    status         = Column(SAEnum(ValidationStatus, native_enum=False), nullable=False)
    metrics        = Column(SmartJSON(), nullable=True)
    raw_logs       = Column(Text, nullable=True)
    error_log      = Column(Text, nullable=True)
    duration_ms    = Column(Integer, nullable=True)
    signoff_id     = Column(GUID, ForeignKey("production_signoffs.id"), nullable=True)
    created_at     = Column(DateTime(timezone=True), default=utcnow, nullable=False)

class HandoverEvent(Base):
    __tablename__ = "handover_events"
    __table_args__ = {"extend_existing": True}
    id             = Column(GUID, primary_key=True, default=uuid.uuid4)
    asset_id       = Column(String(100), nullable=False, index=True)
    from_owner     = Column(String(100), nullable=False)
    to_owner       = Column(String(100), nullable=False)
    handover_type  = Column(String(50), default="OPERATIONAL")
    context_payload = Column(SmartJSON(), nullable=True)
    created_at     = Column(DateTime(timezone=True), default=utcnow, nullable=False)

class QuorumRequirement(Base):
    __tablename__ = "signoff_quorum_requirements"
    __table_args__ = {"extend_existing": True}
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    component_type = Column(String(100), nullable=False)
    risk_level = Column(String(20), nullable=False)
    required_count = Column(Integer, default=1)

class MultiPartySignoff(Base):
    __tablename__ = "multi_party_signoffs"
    __table_args__ = {"extend_existing": True}
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    signoff_id = Column(GUID, ForeignKey("production_signoffs.id"), nullable=True)
    operator_id = Column(GUID, nullable=False)
    decision = Column(String(20), nullable=False)
    justification = Column(Text, nullable=True)
    signed_at = Column(DateTime(timezone=True), default=utcnow)

class PolicyProposal(Base):
    __tablename__ = "policy_proposals"
    __table_args__ = {"extend_existing": True}
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    policy_code = Column(Text, nullable=False)
    status = Column(String(20), default="PROPOSED")
    created_at = Column(DateTime(timezone=True), default=utcnow)

class GovernorDomain(str, enum.Enum):
    WORKFLOW = "WORKFLOW"
    INCIDENT = "INCIDENT"
    APPROVAL = "APPROVAL"
    POLICY = "POLICY"
    REPAIR = "REPAIR"
    META = "META"

class GovernorCaseRecord(Base):
    __tablename__ = "governor_cases"
    __table_args__ = {"extend_existing": True}
    id                    = Column(GUID, primary_key=True, default=uuid.uuid4)
    project_id            = Column(GUID, nullable=False, index=True)
    project_title         = Column(String(255))
    project_status        = Column(String(50))
    pending_reason        = Column(String(100), nullable=False)
    risk_class            = Column(String(20), nullable=False)
    risk_score            = Column(Integer)
    recommended_decision  = Column(String(50), nullable=False)
    decision_reason_codes = Column(SmartJSON(), default=list)
    has_open_incident     = Column(Integer, default=0)
    has_safety_lock       = Column(Integer, default=0)
    has_active_fingerprint = Column(Integer, default=0)
    requires_prime        = Column(Integer, default=0)
    requires_quorum       = Column(Integer, default=0)
    missing_context       = Column(Integer, default=0)
    stale_seconds         = Column(Integer, default=0)
    snapshot_payload      = Column(SmartJSON())
    created_at            = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    updated_at            = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

class GovernorActionRecord(Base):
    __tablename__ = "governor_actions"
    __table_args__ = {"extend_existing": True}
    id            = Column(GUID, primary_key=True, default=uuid.uuid4)
    case_id       = Column(GUID, nullable=True, index=True)
    project_id    = Column(GUID, nullable=False, index=True)
    action_type   = Column(String(50), nullable=False)
    status        = Column(String(20), default="pending")
    executed_by   = Column(String(100))
    result_payload = Column(SmartJSON(), default=dict)
    justification = Column(Text)
    operator_role = Column(String(50))
    override_flag = Column(Integer, default=0)
    guardrail_bypassed = Column(Integer, default=0)
    approval_snapshot = Column(SmartJSON())
    created_at    = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

class GovernorEscalationRecord(Base):
    __tablename__ = "governor_escalations"
    __table_args__ = {"extend_existing": True}
    id              = Column(GUID, primary_key=True, default=uuid.uuid4)
    case_id         = Column(GUID, nullable=True, index=True)
    project_id      = Column(GUID, nullable=False, index=True)
    escalation_type = Column(String(50), nullable=False)
    target_role     = Column(String(50), nullable=False)
    reason          = Column(Text)
    status          = Column(String(20), default="open")
    resolution_type = Column(String(50))
    resolution_notes = Column(Text)
    resolved_by     = Column(String(100))
    final_action    = Column(String(50))
    created_at      = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    resolved_at     = Column(DateTime(timezone=True))

class GovernorDecisionQuality(str, enum.Enum):
    CORRECT = "CORRECT"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    FALSE_NEGATIVE = "FALSE_NEGATIVE"
    PARTIAL = "PARTIAL"
    STALE = "STALE"

class GovernorOutcomeType(str, enum.Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    PARTIAL = "PARTIAL"
    REGRESSION = "REGRESSION"
    IMPROVEMENT = "IMPROVEMENT"

class GovernorOutcomeQuality(str, enum.Enum):
    OPTIMAL = "OPTIMAL"
    SUBOPTIMAL = "SUBOPTIMAL"
    REDUNDANT = "REDUNDANT"
    RISKY = "RISKY"
    VETOED_LATER = "VETOED_LATER"

class GovernorOutcomeRecord(Base):
    __tablename__ = "governor_outcomes"
    __table_args__ = {"extend_existing": True}
    id                    = Column(GUID, primary_key=True, default=uuid.uuid4)
    case_id               = Column(GUID, nullable=True, index=True)
    project_id            = Column(GUID, nullable=False, index=True)
    action_id             = Column(GUID, nullable=True, index=True)
    decision              = Column(String(50))
    final_outcome         = Column(SAEnum(GovernorOutcomeType, native_enum=False), nullable=False)
    quality               = Column(SAEnum(GovernorOutcomeQuality, native_enum=False), nullable=False)
    was_successful        = Column(Integer, default=1)
    operator_overrode     = Column(Integer, default=0)
    operator_agreed       = Column(Integer, default=1)
    resolution_latency_seconds = Column(Integer, default=0)
    reason_codes          = Column(SmartJSON(), default=list)
    created_at            = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

class CalibrationStatus(str, enum.Enum):
    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"
    APPLIED = "APPLIED"
    REJECTED = "REJECTED"
    ROLLED_BACK = "ROLLED_BACK"

class GovernorCalibrationRecord(Base):
    __tablename__ = "governor_calibrations"
    __table_args__ = {"extend_existing": True}
    id               = Column(GUID, primary_key=True, default=uuid.uuid4)
    parameter_name   = Column(String(100), nullable=False, index=True)
    old_value        = Column(Float, nullable=False)
    proposed_value   = Column(Float, nullable=False)
    applied_value    = Column(Float, nullable=True)
    change_reason    = Column(Text, nullable=True)
    confidence_score = Column(Float, default=0.0)
    window_days      = Column(Integer, default=14)
    sample_size      = Column(Integer, default=0)
    status           = Column(SAEnum(CalibrationStatus, native_enum=False), default=CalibrationStatus.PROPOSED, index=True)
    approved_by      = Column(String(100), nullable=True)
    rolled_back_from = Column(GUID, nullable=True)
    created_at       = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    applied_at       = Column(DateTime(timezone=True), nullable=True)

class GovernorConflictType(str, enum.Enum):
    NONE = "NONE"
    RISK_DISAGREEMENT = "RISK_DISAGREEMENT"
    ACTION_DISAGREEMENT = "ACTION_DISAGREEMENT"
    POLICY_BLOCK = "POLICY_BLOCK"
    QUORUM_REQUIRED = "QUORUM_REQUIRED"
    PRIME_REQUIRED = "PRIME_REQUIRED"

class MetaGovernorDecisionType(str, enum.Enum):
    ACCEPT_DOMAIN_DECISION = "ACCEPT_DOMAIN_DECISION"
    BLOCK_AND_ESCALATE = "BLOCK_AND_ESCALATE"
    MERGE_WITH_CONSTRAINTS = "MERGE_WITH_CONSTRAINTS"
    REQUIRES_PRIME_REVIEW = "REQUIRES_PRIME_REVIEW"
    REQUIRES_QUORUM = "REQUIRES_QUORUM"
    NO_ACTION = "NO_ACTION"

class GovernorConflictRecord(Base):
    __tablename__ = "governor_conflicts"
    __table_args__ = {"extend_existing": True}
    id               = Column(GUID, primary_key=True, default=uuid.uuid4)
    project_id       = Column(GUID, nullable=False, index=True)
    case_id          = Column(GUID, nullable=True, index=True)
    domain_a         = Column(SAEnum(GovernorDomain, native_enum=False), nullable=False)
    domain_b         = Column(SAEnum(GovernorDomain, native_enum=False), nullable=False)
    decision_a       = Column(String(64), nullable=False)
    decision_b       = Column(String(64), nullable=False)
    conflict_type    = Column(SAEnum(GovernorConflictType, native_enum=False), nullable=False, index=True)
    conflict_summary = Column(Text, nullable=True)
    status           = Column(String(16), default="open")
    created_at       = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    resolved_at      = Column(DateTime(timezone=True), nullable=True)

class MetaGovernorDecisionRecord(Base):
    __tablename__ = "meta_governor_decisions"
    __table_args__ = {"extend_existing": True}
    id                = Column(GUID, primary_key=True, default=uuid.uuid4)
    project_id        = Column(GUID, nullable=False, index=True)
    case_id           = Column(GUID, nullable=True, index=True)
    winning_domain    = Column(SAEnum(GovernorDomain, native_enum=False), nullable=True)
    final_decision    = Column(String(64), nullable=False)
    final_risk_class  = Column(String(16), nullable=False)
    reason_codes      = Column(SmartJSON(), default=list)
    applied_constraints = Column(SmartJSON(), default=list)
    created_at        = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

class GovernorRuntimeStatus(str, enum.Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    FROZEN = "FROZEN"
    ISOLATED = "ISOLATED"
    FAILED = "FAILED"

class GovernorDrillType(str, enum.Enum):
    DOMAIN_TIMEOUT = "DOMAIN_TIMEOUT"
    META_TIMEOUT = "META_TIMEOUT"
    CONFLICT_STORM = "CONFLICT_STORM"
    FALSE_ESCALATION_BURST = "FALSE_ESCALATION_BURST"
    REPLAY_STORM = "REPLAY_STORM"
    POLICY_VETO_FLOOD = "POLICY_VETO_FLOOD"
    LINEAGE_FAILURE = "LINEAGE_FAILURE"
    DB_DEGRADED = "DB_DEGRADED"

class GovernorDrillStatus(str, enum.Enum):
    PLANNED = "PLANNED"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"

class GovernorRuntimeRecord(Base):
    __tablename__ = "governor_runtime"
    __table_args__ = {"extend_existing": True}
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    domain = Column(SAEnum(GovernorDomain, native_enum=False), nullable=False, index=True)
    runtime_status = Column(SAEnum(GovernorRuntimeStatus, native_enum=False), nullable=False, index=True)
    reason = Column(Text, nullable=True)
    freeze_mode = Column(Integer, default=0)
    advisory_only = Column(Integer, default=0)
    last_healthy_at = Column(DateTime(timezone=True), nullable=True)
    last_failure_at = Column(DateTime(timezone=True), nullable=True)
    failure_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

class GovernorDrillRecord(Base):
    __tablename__ = "governor_drills"
    __table_args__ = {"extend_existing": True}
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    drill_type = Column(SAEnum(GovernorDrillType, native_enum=False), nullable=False, index=True)
    target_domain = Column(SAEnum(GovernorDomain, native_enum=False), nullable=True)
    status = Column(SAEnum(GovernorDrillStatus, native_enum=False), nullable=False, index=True)
    scenario_payload = Column(SmartJSON(), nullable=True)
    result_payload = Column(SmartJSON(), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

class GovernorSloSampleRecord(Base):
    __tablename__ = "governor_slo_samples"
    __table_args__ = {"extend_existing": True}
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    domain = Column(SAEnum(GovernorDomain, native_enum=False), nullable=False, index=True)
    operation_name = Column(String(64), nullable=False, index=True)
    latency_ms = Column(Integer, nullable=False)
    success = Column(Integer, default=1)
    sample_window = Column(Integer, default=60)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

class GovernorCircuitBreakerRecord(Base):
    __tablename__ = "governor_circuit_breakers"
    __table_args__ = {"extend_existing": True}
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    domain = Column(SAEnum(GovernorDomain, native_enum=False), nullable=False, index=True)
    state = Column(String(16), nullable=False, index=True)
    trigger_reason = Column(Text, nullable=True)
    opened_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    failure_threshold = Column(Integer, default=5)
    recovery_mode = Column(String(16), default="AUTO")
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

class PolicyEvolutionStatus(str, enum.Enum):
    PROPOSED = "PROPOSED"
    SIMULATED = "SIMULATED"
    APPROVED = "APPROVED"
    APPLIED = "APPLIED"
    REJECTED = "REJECTED"
    ROLLED_BACK = "ROLLED_BACK"

class PolicyEvolutionType(str, enum.Enum):
    RULE_CHANGE = "RULE_CHANGE"
    VETO_PRIORITY_CHANGE = "VETO_PRIORITY_CHANGE"
    ESCALATION_POLICY_CHANGE = "ESCALATION_POLICY_CHANGE"
    ARCHIVE_POLICY_CHANGE = "ARCHIVE_POLICY_CHANGE"
    REPLAY_POLICY_CHANGE = "REPLAY_POLICY_CHANGE"
    CONFLICT_RESOLUTION_CHANGE = "CONFLICT_RESOLUTION_CHANGE"

class PolicyEvidenceType(str, enum.Enum):
    FALSE_POSITIVE_CLUSTER = "FALSE_POSITIVE_CLUSTER"
    FALSE_NEGATIVE_CLUSTER = "FALSE_NEGATIVE_CLUSTER"
    OPERATOR_DISAGREEMENT = "OPERATOR_DISAGREEMENT"
    HIGH_ESCALATION_RATE = "HIGH_ESCALATION_RATE"
    LOW_REPLAY_SUCCESS = "LOW_REPLAY_SUCCESS"
    SLO_BREACH_PATTERN = "SLO_BREACH_PATTERN"

class GovernorPolicyEvolutionRecord(Base):
    __tablename__ = "governor_policy_evolutions"
    __table_args__ = {"extend_existing": True}
    id               = Column(GUID, primary_key=True, default=uuid.uuid4)
    policy_key       = Column(String(100), nullable=False, index=True)
    evolution_type   = Column(SAEnum(PolicyEvolutionType, native_enum=False), nullable=False, index=True)
    old_value        = Column(SmartJSON(), nullable=True)
    proposed_value   = Column(SmartJSON(), nullable=False)
    applied_value    = Column(SmartJSON(), nullable=True)
    change_reason    = Column(Text, nullable=True)
    evidence_summary = Column(SmartJSON(), nullable=True)
    confidence_score = Column(Float, default=0.0)
    status           = Column(SAEnum(PolicyEvolutionStatus, native_enum=False), default=PolicyEvolutionStatus.PROPOSED, index=True)
    proposed_by      = Column(String(100), default="SYSTEM")
    approved_by      = Column(String(100), nullable=True)
    rolled_back_from = Column(GUID, nullable=True)
    created_at       = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    applied_at       = Column(DateTime(timezone=True), nullable=True)

class GovernorPolicySimulationRecord(Base):
    __tablename__ = "governor_policy_simulations"
    __table_args__ = {"extend_existing": True}
    id                          = Column(GUID, primary_key=True, default=uuid.uuid4)
    evolution_id                = Column(GUID, ForeignKey("governor_policy_evolutions.id"), nullable=False, index=True)
    simulation_window_days      = Column(Integer, default=14)
    sample_size                 = Column(Integer, default=0)
    predicted_accuracy_delta    = Column(Float, default=0.0)
    predicted_false_positive_delta = Column(Float, default=0.0)
    predicted_false_negative_delta = Column(Float, default=0.0)
    predicted_escalation_delta   = Column(Float, default=0.0)
    predicted_latency_delta      = Column(Float, default=0.0)
    result_payload              = Column(SmartJSON(), nullable=True)
    created_at                  = Column(DateTime(timezone=True), default=utcnow, nullable=False)

class GovernorPolicySnapshotRecord(Base):
    __tablename__ = "governor_policy_snapshots"
    __table_args__ = {"extend_existing": True}
    id            = Column(GUID, primary_key=True, default=uuid.uuid4)
    snapshot_name = Column(String(200), nullable=False)
    policy_payload = Column(SmartJSON(), nullable=False)
    created_by    = Column(String(100), default="SYSTEM")
    created_at    = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

class GovernorAlertSeverity(str, enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class GovernorAlertStatus(str, enum.Enum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    SUPPRESSED = "SUPPRESSED"

class GovernorAlertType(str, enum.Enum):
    DECISION_ACCURACY_DROP = "DECISION_ACCURACY_DROP"
    FALSE_POSITIVE_SPIKE = "FALSE_POSITIVE_SPIKE"
    FALSE_NEGATIVE_SPIKE = "FALSE_NEGATIVE_SPIKE"
    POLICY_CHURN_SPIKE = "POLICY_CHURN_SPIKE"
    META_CONFLICT_RATE_SPIKE = "META_CONFLICT_RATE_SPIKE"
    REPLAY_SUCCESS_REGRESSION = "REPLAY_SUCCESS_REGRESSION"
    DOMAIN_TIMEOUT_BURST = "DOMAIN_TIMEOUT_BURST"
    CIRCUIT_BREAKER_OPEN_RATE = "CIRCUIT_BREAKER_OPEN_RATE"
    FREEZE_MODE_DURATION = "FREEZE_MODE_DURATION"
    DRIFT_DETECTED = "DRIFT_DETECTED"

class GovernorDriftType(str, enum.Enum):
    RISK_DRIFT = "RISK_DRIFT"
    DECISION_DRIFT = "DECISION_DRIFT"
    DOMAIN_DISAGREEMENT_DRIFT = "DOMAIN_DISAGREEMENT_DRIFT"
    POLICY_DRIFT = "POLICY_DRIFT"
    LATENCY_DRIFT = "LATENCY_DRIFT"

class GovernorAlertRecord(Base):
    __tablename__ = "governor_alerts"
    __table_args__ = {"extend_existing": True}
    id               = Column(GUID, primary_key=True, default=uuid.uuid4)
    alert_type       = Column(SAEnum(GovernorAlertType, native_enum=False), nullable=False, index=True)
    severity         = Column(SAEnum(GovernorAlertSeverity, native_enum=False), nullable=False, index=True)
    status           = Column(SAEnum(GovernorAlertStatus, native_enum=False), default=GovernorAlertStatus.OPEN, index=True)
    domain           = Column(SAEnum(GovernorDomain, native_enum=False), nullable=True, index=True)
    title            = Column(String(200), nullable=False)
    summary          = Column(Text, nullable=True)
    metric_value     = Column(Float, nullable=True)
    threshold_value  = Column(Float, nullable=True)
    evidence_payload = Column(SmartJSON(), nullable=True)
    opened_at        = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    acknowledged_at  = Column(DateTime(timezone=True), nullable=True)
    resolved_at      = Column(DateTime(timezone=True), nullable=True)
    owner_id         = Column(String(100), nullable=True)

class GovernorMetricAggregateRecord(Base):
    __tablename__ = "governor_metric_aggregates"
    __table_args__ = {"extend_existing": True}
    id               = Column(GUID, primary_key=True, default=uuid.uuid4)
    metric_key       = Column(String(100), nullable=False, index=True)
    domain           = Column(SAEnum(GovernorDomain, native_enum=False), nullable=True, index=True)
    window_minutes   = Column(Integer, default=60)
    sample_size      = Column(Integer, default=0)
    value            = Column(Float, nullable=False)
    baseline_value   = Column(Float, nullable=True)
    delta_value      = Column(Float, nullable=True)
    created_at       = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

class GovernorDriftRecord(Base):
    __tablename__ = "governor_drifts"
    __table_args__ = {"extend_existing": True}
    id                  = Column(GUID, primary_key=True, default=uuid.uuid4)
    drift_type          = Column(SAEnum(GovernorDriftType, native_enum=False), nullable=False, index=True)
    domain              = Column(SAEnum(GovernorDomain, native_enum=False), nullable=True, index=True)
    baseline_window_days = Column(Integer, default=14)
    current_window_days  = Column(Integer, default=1)
    drift_score         = Column(Float, default=0.0)
    summary             = Column(Text, nullable=True)
    evidence_payload    = Column(SmartJSON(), nullable=True)
    created_at          = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

class ProofEventType(str, enum.Enum):
    GOVERNOR_DECISION = "GOVERNOR_DECISION"
    META_DECISION = "META_DECISION"
    CONFLICT_EVENT = "CONFLICT_EVENT"
    POLICY_EVOLUTION = "POLICY_EVOLUTION"
    ALERT_EVENT = "ALERT_EVENT"
    DRIFT_EVENT = "DRIFT_EVENT"
    RUNTIME_EVENT = "RUNTIME_EVENT"
    OVERRIDE_EVENT = "OVERRIDE_EVENT"
    CALIBRATION_EVENT = "CALIBRATION_EVENT"
    SNAPSHOT_SEAL = "SNAPSHOT_SEAL"
    # Phase 12: Fleet Events
    AGENT_ASSIGNED = "AGENT_ASSIGNED"
    AGENT_RELEASED = "AGENT_RELEASED"
    CLUSTER_FROZEN = "CLUSTER_FROZEN"
    FLEET_REBALANCED = "FLEET_REBALANCED"
    BUDGET_BLOCK = "BUDGET_BLOCK"
    AGENT_QUARANTINED = "AGENT_QUARANTINED"

class ProofSealStatus(str, enum.Enum):
    PENDING = "PENDING"
    SEALED = "SEALED"
    VERIFIED = "VERIFIED"
    BROKEN = "BROKEN"

class GovernanceProofEventRecord(Base):
    __tablename__ = "governance_proof_events"
    __table_args__ = {'extend_existing': True}
    id             = Column(GUID, primary_key=True, default=uuid.uuid4)
    event_type       = Column(SAEnum(ProofEventType, native_enum=False), nullable=False, index=True)
    domain           = Column(SAEnum(GovernorDomain, native_enum=False), nullable=True, index=True)
    entity_id        = Column(String(100), nullable=True, index=True)
    payload_hash     = Column(String(64), nullable=False)
    payload_canonical = Column(Text, nullable=False)
    prev_event_hash  = Column(String(64), nullable=True)
    event_hash       = Column(String(64), nullable=False, index=True)
    chain_index      = Column(BigInteger, nullable=False, index=True)
    created_at       = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    created_by       = Column(String(100), nullable=True)

class GovernanceProofSnapshotRecord(Base):
    __tablename__ = "governance_proof_snapshots"
    __table_args__ = {'extend_existing': True}
    id                 = Column(GUID, primary_key=True, default=uuid.uuid4)
    snapshot_name    = Column(String(200), nullable=False)
    start_chain_index = Column(BigInteger, nullable=False)
    end_chain_index   = Column(BigInteger, nullable=False)
    event_count       = Column(Integer, default=0)
    merkle_root       = Column(String(64), nullable=False)
    snapshot_hash     = Column(String(64), nullable=False)
    seal_status      = Column(SAEnum(ProofSealStatus, native_enum=False), default=ProofSealStatus.PENDING, index=True)
    created_at       = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    sealed_by        = Column(String(100), nullable=True)

class GovernanceMerkleNodeRecord(Base):
    __tablename__ = "governance_merkle_nodes"
    __table_args__ = {'extend_existing': True}
    id             = Column(GUID, primary_key=True, default=uuid.uuid4)
    snapshot_id      = Column(GUID, nullable=False, index=True)
    node_level       = Column(Integer, nullable=False)
    node_index       = Column(Integer, nullable=False)
    left_hash        = Column(String(64), nullable=True)
    right_hash       = Column(String(64), nullable=True)
    node_hash        = Column(String(64), nullable=False)

class GovernanceProofVerificationRecord(Base):
    __tablename__ = "governance_proof_verifications"
    __table_args__ = {'extend_existing': True}
    id                  = Column(GUID, primary_key=True, default=uuid.uuid4)
    target_type        = Column(String(50), nullable=False)
    target_id          = Column(String(100), nullable=False, index=True)
    snapshot_id        = Column(GUID, nullable=True, index=True)
    verification_status = Column(SAEnum(ProofSealStatus, native_enum=False), nullable=False)
    proof_payload      = Column(SmartJSON(), nullable=True)
    verified_at        = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    verified_by        = Column(String(100), nullable=True)
