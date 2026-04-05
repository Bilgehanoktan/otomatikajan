"""
RepairJob — Tüm repair pipeline'ının durum makinesi.

Durum geçişleri:
NEW -> INCIDENT_COLLECTED -> TRIAGED -> CONTEXT_BUILT -> ROOT_CAUSE_ANALYZED
    -> PATCH_PLANNED -> PATCH_GENERATED -> REVIEWED -> VERIFIED
    -> PR_CREATED -> AWAITING_APPROVAL -> MERGED | REJECTED | ROLLED_BACK

Hata durumları:
FAILED_TRIAGE | FAILED_ANALYSIS | FAILED_PATCH_GENERATION
FAILED_VALIDATION | REQUIRES_MANUAL_REVIEW
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class RepairJobStatus(str, Enum):
    NEW                    = "new"
    INCIDENT_COLLECTED     = "incident_collected"
    TRIAGED                = "triaged"
    CONTEXT_BUILT          = "context_built"
    ROOT_CAUSE_ANALYZED    = "root_cause_analyzed"
    PATCH_PLANNED          = "patch_planned"
    PATCH_GENERATED        = "patch_generated"
    REVIEWED               = "reviewed"
    VERIFIED               = "verified"
    # Canary durumları (Faz 11)
    CANARY_PENDING         = "canary_pending"
    CANARY_RUNNING         = "canary_running"
    CANARY_PASSED          = "canary_passed"
    CANARY_FAILED          = "canary_failed"
    VECTOR_CONTEXT_LOADED  = "vector_context_loaded"
    GENERATED_TESTS_READY  = "generated_tests_ready"
    SANDBOX_VERIFIED       = "sandbox_verified"
    LESSON_SAVED           = "lesson_saved"
    PR_CREATED             = "pr_created"
    AWAITING_APPROVAL      = "awaiting_approval"
    MERGED                 = "merged"
    REJECTED               = "rejected"
    ROLLED_BACK            = "rolled_back"
    # Hata durumları
    FAILED_TRIAGE          = "failed_triage"
    FAILED_ANALYSIS        = "failed_analysis"
    FAILED_PATCH_GENERATION = "failed_patch_generation"
    FAILED_VALIDATION      = "failed_validation"
    REQUIRES_MANUAL_REVIEW = "requires_manual_review"


# Geçerli durum geçişleri
VALID_TRANSITIONS: dict[RepairJobStatus, list[RepairJobStatus]] = {
    RepairJobStatus.NEW: [RepairJobStatus.INCIDENT_COLLECTED, RepairJobStatus.REJECTED],
    RepairJobStatus.INCIDENT_COLLECTED: [RepairJobStatus.TRIAGED, RepairJobStatus.FAILED_TRIAGE, RepairJobStatus.REQUIRES_MANUAL_REVIEW, RepairJobStatus.REJECTED],
    RepairJobStatus.TRIAGED: [RepairJobStatus.CONTEXT_BUILT, RepairJobStatus.FAILED_ANALYSIS, RepairJobStatus.REQUIRES_MANUAL_REVIEW, RepairJobStatus.REJECTED],
    RepairJobStatus.CONTEXT_BUILT: [RepairJobStatus.ROOT_CAUSE_ANALYZED, RepairJobStatus.FAILED_ANALYSIS],
    RepairJobStatus.ROOT_CAUSE_ANALYZED: [RepairJobStatus.PATCH_PLANNED, RepairJobStatus.REQUIRES_MANUAL_REVIEW],
    RepairJobStatus.PATCH_PLANNED: [RepairJobStatus.PATCH_GENERATED, RepairJobStatus.FAILED_PATCH_GENERATION, RepairJobStatus.REQUIRES_MANUAL_REVIEW],
    RepairJobStatus.PATCH_GENERATED: [RepairJobStatus.REVIEWED, RepairJobStatus.REJECTED],
    RepairJobStatus.REVIEWED: [RepairJobStatus.VERIFIED, RepairJobStatus.REJECTED, RepairJobStatus.REQUIRES_MANUAL_REVIEW],
    RepairJobStatus.VERIFIED: [
        RepairJobStatus.CANARY_PENDING,     # Canary aktifse
        RepairJobStatus.PR_CREATED,         # Canary pasifse direkt PR
        RepairJobStatus.FAILED_VALIDATION,
        RepairJobStatus.REJECTED,
    ],
    RepairJobStatus.CANARY_PENDING:  [RepairJobStatus.CANARY_RUNNING, RepairJobStatus.REJECTED],
    RepairJobStatus.CANARY_RUNNING:  [RepairJobStatus.CANARY_PASSED, RepairJobStatus.CANARY_FAILED],
    RepairJobStatus.CANARY_PASSED:   [RepairJobStatus.PR_CREATED],
    RepairJobStatus.CANARY_FAILED:   [RepairJobStatus.REQUIRES_MANUAL_REVIEW, RepairJobStatus.REJECTED],
    RepairJobStatus.PR_CREATED: [RepairJobStatus.AWAITING_APPROVAL],
    RepairJobStatus.AWAITING_APPROVAL: [RepairJobStatus.MERGED, RepairJobStatus.REJECTED, RepairJobStatus.ROLLED_BACK],
}

# Terminal durumlar — geçiş olmaz
TERMINAL_STATES = {
    RepairJobStatus.MERGED,
    RepairJobStatus.REJECTED,
    RepairJobStatus.ROLLED_BACK,
    RepairJobStatus.REQUIRES_MANUAL_REVIEW,
}


@dataclass
class RepairJob:
    job_id:        str
    incident_id:   str
    status:        RepairJobStatus = RepairJobStatus.NEW
    ticket_id:     Optional[str]   = None
    plan_id:       Optional[str]   = None
    validation_id: Optional[str]   = None
    pr_url:        Optional[str]   = None
    branch_name:   Optional[str]   = None
    diff:           str             = ""
    error_detail:   str             = ""
    # Faz 11 alanları
    canary_id:      Optional[str]   = None
    canary_status:  Optional[str]   = None
    generated_tests: list[dict]     = field(default_factory=list)
    fingerprint_hash: Optional[str] = None
    duplicate_of:   Optional[str]   = None
    risk_score:     int             = 0
    # Faz 12 RC1 yeni alanlar
    vector_context_used: bool        = False
    vector_context_summary: str      = ""
    debate_triggered:   bool         = False
    debate_result_summary: str       = ""
    debate_winning_hypothesis: str   = ""
    sandbox_verified:   bool         = False
    sandbox_output:     str          = ""
    lesson_saved:       bool         = False
    ranker_adjusted:    bool         = False
    ranker_raw_confidence: int       = 0
    ranker_adjusted_confidence: int  = 0
    simulation_mode: bool           = False
    history:        list[dict]      = field(default_factory=list)
    created_at:    datetime        = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at:    datetime        = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(cls, incident_id: str) -> "RepairJob":
        return cls(
            job_id=f"rjob_{uuid.uuid4().hex[:8]}",
            incident_id=incident_id,
        )

    def transition(self, new_status: RepairJobStatus, note: str = "") -> bool:
        """Geçerli durumdan yeni duruma geç. Geçersizse False döner."""
        if self.status in TERMINAL_STATES:
            return False
        allowed = VALID_TRANSITIONS.get(self.status, [])
        if new_status not in allowed:
            return False
        self.history.append({
            "from":   self.status.value,
            "to":     new_status.value,
            "note":   note,
            "at":     datetime.now(timezone.utc).isoformat(),
        })
        self.status = new_status
        self.updated_at = datetime.now(timezone.utc)
        return True

    def is_terminal(self) -> bool:
        return self.status in TERMINAL_STATES

    def to_dict(self) -> dict:
        return {
            "job_id":          self.job_id,
            "incident_id":     self.incident_id,
            "status":          self.status.value,
            "ticket_id":       self.ticket_id,
            "plan_id":         self.plan_id,
            "validation_id":   self.validation_id,
            "pr_url":          self.pr_url,
            "branch_name":     self.branch_name,
            "error_detail":    self.error_detail,
            "canary_id":       self.canary_id,
            "canary_status":   self.canary_status,
            "generated_tests": self.generated_tests,
            "fingerprint_hash": self.fingerprint_hash,
            "duplicate_of":    self.duplicate_of,
            "risk_score":      self.risk_score,
            "vector_context_used": self.vector_context_used,
            "vector_context_summary": self.vector_context_summary,
            "debate_triggered": self.debate_triggered,
            "debate_result_summary": self.debate_result_summary,
            "debate_winning_hypothesis": self.debate_winning_hypothesis,
            "sandbox_verified": self.sandbox_verified,
            "lesson_saved":     self.lesson_saved,
            "ranker_adjusted":  self.ranker_adjusted,
            "ranker_adjusted_confidence": self.ranker_adjusted_confidence,
            "simulation_mode": self.simulation_mode,
            "history":         self.history,
            "created_at":      self.created_at.isoformat(),
            "updated_at":      self.updated_at.isoformat(),
        }
