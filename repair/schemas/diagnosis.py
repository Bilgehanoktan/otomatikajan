"""
DiagnosisTicket — Triage katmanının çıktısı.
Incident'ten sınıflandırılmış, dosya listeli, mod kararı verilmiş bilet.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class ProblemClass(str, Enum):
    IMPORT_ERROR          = "import_error"
    INTERFACE_MISMATCH    = "interface_mismatch"
    SCHEMA_MISMATCH       = "schema_mismatch"
    CONTRACT_BROKEN       = "contract_broken"
    NULL_STATE_ERROR      = "null_state_error"
    ROUTE_ERROR           = "route_error"
    AUTH_FAILURE          = "auth_failure"
    QUEUE_FAILURE         = "queue_failure"
    CONFIG_ERROR          = "config_error"
    PERFORMANCE_REGRESSION = "performance_regression"
    SECURITY_VIOLATION    = "security_violation"
    TEST_REGRESSION       = "test_regression"
    ARCHITECTURAL_DEBT    = "architectural_debt"
    SUBSYSTEM_CREATION    = "subsystem_creation"
    UNKNOWN               = "unknown"


class RepairMode(str, Enum):
    AUTO_PATCH_PR    = "auto_patch_pr_only"   # patch üret, PR aç, merge yok
    MANUAL_ONLY      = "manual_only"          # sadece analiz raporu
    REJECT           = "reject"               # oto-patch uygun değil


@dataclass
class RootCauseHypothesis:
    id:                    str
    title:                 str
    explanation:           str
    supporting_evidence:   list[str] = field(default_factory=list)
    contradicting_evidence: list[str] = field(default_factory=list)
    confidence:            int = 0   # 0-100

    def to_dict(self) -> dict:
        return {
            "id":                     self.id,
            "title":                  self.title,
            "explanation":            self.explanation,
            "supporting_evidence":    self.supporting_evidence,
            "contradicting_evidence": self.contradicting_evidence,
            "confidence":             self.confidence,
        }


@dataclass
class DiagnosisTicket:
    """Triage + Root Cause sonucu."""

    ticket_id:            str
    incident_id:          str
    classification:       ProblemClass
    severity:             str
    candidate_files:      list[str]       = field(default_factory=list)
    candidate_symbols:    list[str]       = field(default_factory=list)
    hypotheses:           list[RootCauseHypothesis] = field(default_factory=list)
    selected_hypothesis:  Optional[RootCauseHypothesis] = None
    recommended_mode:     RepairMode      = RepairMode.MANUAL_ONLY
    requires_human:       bool            = True
    rationale:            str             = ""
    created_at:           datetime        = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(cls, incident_id: str, classification: ProblemClass, severity: str, **kwargs) -> "DiagnosisTicket":
        return cls(
            ticket_id=f"diag_{uuid.uuid4().hex[:8]}",
            incident_id=incident_id,
            classification=classification,
            severity=severity,
            **kwargs,
        )

    def to_dict(self) -> dict:
        return {
            "ticket_id":           self.ticket_id,
            "incident_id":         self.incident_id,
            "classification":      self.classification.value,
            "severity":            self.severity,
            "candidate_files":     self.candidate_files,
            "candidate_symbols":   self.candidate_symbols,
            "hypotheses":          [h.to_dict() for h in self.hypotheses],
            "selected_hypothesis": self.selected_hypothesis.to_dict() if self.selected_hypothesis else None,
            "recommended_mode":    self.recommended_mode.value,
            "requires_human":      self.requires_human,
            "rationale":           self.rationale,
            "created_at":          self.created_at.isoformat(),
        }
