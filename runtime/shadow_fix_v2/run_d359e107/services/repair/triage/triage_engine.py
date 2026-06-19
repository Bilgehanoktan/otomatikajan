"""
Triage Engine
IncidentRecord -> DiagnosisTicket

Görevler:
1. Problem sınıfını belirle (import_error, contract_broken vs.)
2. Repair modunu belirle (auto_patch_pr, manual_only, reject)
3. Candidate dosyaları listele
4. Requires human belirleme
"""

from services.repair.schemas.incident import IncidentRecord, IncidentSeverity
from services.repair.schemas.diagnosis import DiagnosisTicket, ProblemClass, RepairMode


# ── Sınıflandırma Kuralları ────────────────────────────────────
_CLASSIFICATION_RULES: list[tuple[ProblemClass, list[str]]] = [
    (ProblemClass.IMPORT_ERROR,       ["ImportError", "ModuleNotFoundError", "cannot import", "NameError"]),
    (ProblemClass.AUTH_FAILURE,       ["401", "403", "Unauthorized", "jwt", "token", "bcrypt", "auth"]),
    (ProblemClass.SCHEMA_MISMATCH,    ["pydantic", "ValidationError", "schema", "Field required", "json"]),
    (ProblemClass.CONTRACT_BROKEN,    ["TypeError", "AttributeError", "has no attribute", "unexpected keyword"]),
    (ProblemClass.ROUTE_ERROR,        ["404", "422", "endpoint", "router", "route", "path"]),
    (ProblemClass.NULL_STATE_ERROR,   ["NoneType", "is None", "null", "KeyError", "IndexError"]),
    (ProblemClass.QUEUE_FAILURE,      ["celery", "redis", "queue", "ConnectionError", "timeout"]),
    (ProblemClass.CONFIG_ERROR,       ["env", ".env", "config", "getenv", "settings", "missing"]),
    (ProblemClass.PERFORMANCE_REGRESSION, ["timeout", "slow", "latency", "p95", "p99"]),
    (ProblemClass.SECURITY_VIOLATION, ["sql injection", "path traversal", "xss", "csrf", "open redirect"]),
    (ProblemClass.TEST_REGRESSION,    ["AssertionError", "FAILED", "test_", "pytest"]),
    (ProblemClass.INTERFACE_MISMATCH, ["interface", "contract", "return type", "signature"]),
]

# ── Manuel Review Gerektiren Durumlar ────────────────────────
_MANUAL_REVIEW_CLASSES = {
    ProblemClass.AUTH_FAILURE,
    ProblemClass.SECURITY_VIOLATION,
}

_MANUAL_REVIEW_MODULES = {
    "auth", "jwt_auth",
}

# ── Otomatik Patch'e Uygun Sınıflar ─────────────────────────
_AUTO_PATCH_CLASSES = {
    ProblemClass.IMPORT_ERROR,
    ProblemClass.NULL_STATE_ERROR,
    ProblemClass.SCHEMA_MISMATCH,
    ProblemClass.CONFIG_ERROR,
    ProblemClass.INTERFACE_MISMATCH,
}


class TriageEngine:
    """
    Incident'i sınıflandırır ve DiagnosisTicket üretir.
    Kod değiştirmez — sadece analiz eder.
    """

    def triage(self, incident: IncidentRecord) -> DiagnosisTicket:
        classification = self._classify(incident)
        mode           = self._decide_mode(incident, classification)
        requires_human = self._requires_human(incident, classification)
        candidate_files = self._candidate_files(incident, classification)
        rationale       = self._build_rationale(incident, classification, mode)

        ticket = DiagnosisTicket.create(
            incident_id=incident.incident_id,
            classification=classification,
            severity=incident.severity.value,
            candidate_files=candidate_files,
            recommended_mode=mode,
            requires_human=requires_human,
            rationale=rationale,
        )
        return ticket

    def _classify(self, incident: IncidentRecord) -> ProblemClass:
        combined = " ".join([
            incident.symptom,
            incident.stack_trace,
            " ".join(incident.log_lines),
        ]).lower()

        for problem_class, keywords in _CLASSIFICATION_RULES:
            if any(kw.lower() in combined for kw in keywords):
                return problem_class

        return ProblemClass.UNKNOWN

    def _decide_mode(self, incident: IncidentRecord, cls: ProblemClass) -> RepairMode:
        # Kritik seviyede her zaman manual
        if incident.severity == IncidentSeverity.CRITICAL:
            return RepairMode.MANUAL_ONLY

        # Auth/security her zaman manual
        if cls in _MANUAL_REVIEW_CLASSES:
            return RepairMode.MANUAL_ONLY

        # Bilinen tehlikeli modüller
        if incident.module in _MANUAL_REVIEW_MODULES:
            return RepairMode.MANUAL_ONLY

        # Oto-patch için uygun sınıflar
        if cls in _AUTO_PATCH_CLASSES:
            return RepairMode.AUTO_PATCH_PR

        return RepairMode.MANUAL_ONLY

    def _requires_human(self, incident: IncidentRecord, cls: ProblemClass) -> bool:
        return (
            cls in _MANUAL_REVIEW_CLASSES
            or incident.module in _MANUAL_REVIEW_MODULES
            or incident.severity in (IncidentSeverity.CRITICAL, IncidentSeverity.HIGH)
        )

    def _candidate_files(self, incident: IncidentRecord, cls: ProblemClass) -> list[str]:
        files = list(incident.suspected_files)

        # Sınıfa göre tipik dosyalar ekle
        class_file_hints: dict[ProblemClass, list[str]] = {
            ProblemClass.IMPORT_ERROR:     ["main.py"],
            ProblemClass.AUTH_FAILURE:     ["auth/jwt_auth.py"],
            ProblemClass.ROUTE_ERROR:      ["api/task_read_router.py", "api/task_write_router.py", "api/task_control_router.py", "api/routes.py"],  # Faz 10.1: split router yapısına güncellendi
            ProblemClass.QUEUE_FAILURE:    ["core/job_queue.py", "tasks/celery_app.py"],
            ProblemClass.CONTRACT_BROKEN:  ["core/orchestrator.py"],
            ProblemClass.SCHEMA_MISMATCH:  ["db/libs.db.models.py", "schemas.py"],
            ProblemClass.CONFIG_ERROR:     ["config.py", ".env.example"],
        }
        hints = class_file_hints.get(cls, [])
        for h in hints:
            if h not in files:
                files.append(h)

        return files[:8]  # maksimum 8 dosya

    def _build_rationale(self, incident: IncidentRecord, cls: ProblemClass, mode: RepairMode) -> str:
        parts = [
            f"Problem sınıfı: {cls.value}",
            f"Tespit: '{incident.symptom[:100]}'",
            f"Modül: {incident.module}",
            f"Repair modu: {mode.value}",
        ]
        if mode == RepairMode.MANUAL_ONLY:
            parts.append("Manuel review gerekçesi: yüksek risk sınıfı veya kritik modül.")
        return " | ".join(parts)


# Singleton
triage_engine = TriageEngine()
