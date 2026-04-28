"""
IncidentRecord — Self-Repair sistemine giren normalize edilmiş olay.
Her hata sinyali (log, CI, test, user feedback) bu şemaya dönüştürülür.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class IncidentSource(str, Enum):
    RUNTIME_LOG    = "runtime_log"
    CI_FAILURE     = "ci_failure"
    TEST_FAILURE   = "test_failure"
    HEALTH_CHECK   = "health_check"
    USER_FEEDBACK  = "user_feedback"
    API_ERROR      = "api_error"
    WORKER_ERROR   = "worker_error"
    MANUAL         = "manual"
    GOVERNANCE     = "governance"


class IncidentSeverity(str, Enum):
    LOW      = "low"
    MEDIUM   = "medium"
    HIGH     = "high"
    CRITICAL = "critical"


@dataclass
class IncidentRecord:
    """Normalize edilmiş olay kaydı — triage + analiz katmanlarına giriş."""

    incident_id:       str
    source:            IncidentSource
    severity:          IncidentSeverity
    service:           str                     # "backend-api", "worker", "telegram-bot"
    module:            str                     # "task_router", "orchestrator"
    symptom:           str                     # "500 Internal Server Error on /api/tasks"
    stack_trace:       str        = ""
    log_lines:         list[str]  = field(default_factory=list)
    suspected_files:   list[str]  = field(default_factory=list)
    failing_tests:     list[str]  = field(default_factory=list)
    reproduction_hint: str        = ""         # "POST /api/v1/projects with title='x'"
    context:           dict       = field(default_factory=dict)
    first_seen_at:     datetime   = field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen_at:      datetime   = field(default_factory=lambda: datetime.now(timezone.utc))
    occurrence_count:  int        = 1
    status:            str        = "open"     # open | triaged | in_repair | resolved | rejected

    @classmethod
    def create(
        cls,
        source: IncidentSource,
        severity: IncidentSeverity,
        service: str,
        module: str,
        symptom: str,
        **kwargs,
    ) -> "IncidentRecord":
        return cls(
            incident_id=f"inc_{uuid.uuid4().hex[:8]}",
            source=source,
            severity=severity,
            service=service,
            module=module,
            symptom=symptom,
            **kwargs,
        )

    def to_dict(self) -> dict:
        return {
            "incident_id":       self.incident_id,
            "source":            self.source.value,
            "severity":          self.severity.value,
            "service":           self.service,
            "module":            self.module,
            "symptom":           self.symptom,
            "stack_trace":       self.stack_trace[:2000],
            "suspected_files":   self.suspected_files,
            "failing_tests":     self.failing_tests,
            "reproduction_hint": self.reproduction_hint,
            "occurrence_count":  self.occurrence_count,
            "status":            self.status,
            "first_seen_at":     self.first_seen_at.isoformat(),
            "last_seen_at":      self.last_seen_at.isoformat(),
        }
