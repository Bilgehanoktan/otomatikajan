"""
Incident Ingestion Layer
Farklı kaynaklardan gelen hata sinyallerini IncidentRecord'a normalize eder.

Kaynaklar:
- runtime exception logları (FastAPI exception handler)
- worker/celery logları
- failed test sonuçları
- health check başarısızlıkları
- kullanıcı geri bildirimi (Telegram /error komutu)
- CI/CD pipeline başarısızlıkları
"""

import re
import uuid
from datetime import datetime, timezone
from typing import Optional, List

from repair.schemas.incident import IncidentRecord, IncidentSource, IncidentSeverity


# ── Kaynak Tespiti ────────────────────────────────────────
_SEVERITY_KEYWORDS = {
    IncidentSeverity.CRITICAL: ["critical", "fatal", "panic", "system exit", "oom", "segfault"],
    IncidentSeverity.HIGH:     ["500", "unhandled exception", "database error", "connection refused",
                                 "authentication failed", "500 internal"],
    IncidentSeverity.MEDIUM:   ["timeout", "rate limit", "429", "503", "502", "warning", "retry"],
    IncidentSeverity.LOW:      ["404", "deprecated", "slow", "info"],
}

_MODULE_PATTERNS = {
    "orchestrator": ["orchestrator", "run_project", "_run_subtask", "dag_node"],
    "task_router":  ["task_router", "task_read_router", "task_write_router", "/api/v1/tasks"],
    "auth":         ["jwt_auth", "login", "refresh_token", "401", "403"],
    "heal_engine":  ["heal_engine", "monitor_loop", "_cycle", "recovery"],
    "llm":          ["model_orchestrator", "complete_task", "provider", "gemini", "openai", "anthropic"],
    "telegram":     ["telegram", "bot.py", "telegram_router"],
    "memory":       ["memory", "retrieval", "context_builder"],
    "worker":       ["celery", "worker", "job_queue", "task_queue"],
    "db":           ["session", "repository", "asyncpg", "sqlalchemy", "PostgreSQL"],
}


def _detect_severity(text: str) -> IncidentSeverity:
    lowered = text.lower()
    for severity, keywords in _SEVERITY_KEYWORDS.items():
        if any(kw in lowered for kw in keywords):
            return severity
    return IncidentSeverity.LOW


def _detect_module(text: str) -> str:
    lowered = text.lower()
    for module, patterns in _MODULE_PATTERNS.items():
        if any(p in lowered for p in patterns):
            return module
    return "unknown"


def _extract_file_paths(text: str) -> list[str]:
    """Stack trace'den dosya yollarını çıkarır."""
    pattern = r'File "([^"]+\.py)"'
    paths = re.findall(pattern, text)
    # Sadece proje dosyaları (site-packages değil)
    return list(dict.fromkeys([
        p for p in paths
        if "site-packages" not in p and "lib/python" not in p
    ]))[:10]


def _extract_exception_type(stack_trace: str) -> str:
    """Son exception tipini çıkarır."""
    match = re.search(r'(\w+Error|\w+Exception):', stack_trace)
    return match.group(1) if match else ""


class IncidentIngestor:
    """
    Farklı giriş kaynaklarından IncidentRecord üretir.
    Tekrar eden hataları gruplar (deduplication).
    """

    def __init__(self):
        self._seen: dict[str, IncidentRecord] = {}  # fingerprint -> incident
        self._hydrated = False

    def _fingerprint(self, symptom: str, module: str) -> str:
        """Aynı hata tekrar gelirse incident güncellenir, yeni üretilmez."""
        return f"{module}::{symptom[:80]}"

    def from_exception(
        self,
        exc: Exception,
        service: str = "backend-api",
        context: Optional[dict] = None,
    ) -> IncidentRecord:
        """FastAPI exception handler'dan gelen hata."""
        import traceback
        stack = traceback.format_exc()
        symptom = f"{type(exc).__name__}: {str(exc)[:200]}"
        module  = _detect_module(stack)
        severity = _detect_severity(stack)
        files   = _extract_file_paths(stack)

        return self._get_or_create(
            source=IncidentSource.RUNTIME_LOG,
            severity=severity,
            service=service,
            module=module,
            symptom=symptom,
            stack_trace=stack,
            suspected_files=files,
            context=context or {},
        )

    def from_log_line(
        self,
        log_line: str,
        service: str = "backend-api",
    ) -> Optional[IncidentRecord]:
        """Tek bir log satırından incident üretmeyi dene."""
        severity = _detect_severity(log_line)
        if severity == IncidentSeverity.LOW:
            return None   # düşük önemlileri ignore et
        module = _detect_module(log_line)
        return self._get_or_create(
            source=IncidentSource.RUNTIME_LOG,
            severity=severity,
            service=service,
            module=module,
            symptom=log_line[:300],
        )

    def from_failed_test(
        self,
        test_name: str,
        test_output: str,
        service: str = "tests",
    ) -> IncidentRecord:
        """pytest başarısızlığından incident."""
        module = _detect_module(test_output)
        severity = _detect_severity(test_output)
        files = _extract_file_paths(test_output)
        return self._get_or_create(
            source=IncidentSource.TEST_FAILURE,
            severity=severity,
            service=service,
            module=module,
            symptom=f"Test başarısız: {test_name}",
            stack_trace=test_output,
            suspected_files=files,
            failing_tests=[test_name],
        )

    def from_health_check(
        self,
        failing_service: str,
        detail: str,
    ) -> IncidentRecord:
        """Health check başarısızlığından incident."""
        return self._get_or_create(
            source=IncidentSource.HEALTH_CHECK,
            severity=IncidentSeverity.HIGH,
            service=failing_service,
            module=_detect_module(detail),
            symptom=f"Health check başarısız: {failing_service} — {detail[:100]}",
        )

    def from_dict(self, data: dict) -> IncidentRecord:
        """API üzerinden manuel oluşturma."""
        return self._get_or_create(
            source=IncidentSource(data.get("source", "manual")),
            severity=IncidentSeverity(data.get("severity", "medium")),
            service=data.get("service", "unknown"),
            module=data.get("module", "unknown"),
            symptom=data.get("symptom", ""),
            stack_trace=data.get("stack_trace", ""),
            suspected_files=data.get("suspected_files", []),
            failing_tests=data.get("failing_tests", []),
            reproduction_hint=data.get("reproduction_hint", ""),
        )

    def _get_or_create(self, **kwargs) -> IncidentRecord:
        fp = self._fingerprint(kwargs.get("symptom", ""), kwargs.get("module", ""))
        if fp in self._seen:
            existing = self._seen[fp]
            existing.occurrence_count += 1
            existing.last_seen_at = datetime.now(timezone.utc)
            return existing
        incident = IncidentRecord.create(**kwargs)
        self._seen[fp] = incident
        return incident

    def list_open(self) -> list[IncidentRecord]:
        return [i for i in self._seen.values() if i.status.lower() == "open"]

    async def hydrate_from_db(self, db_session=None) -> int:
        """Veritabanındaki açık olayları parmak izi (fingerprint) belleğine yükle."""
        if self._hydrated:
            return 0

        count = 0
        try:
            if not db_session:
                from db.session import AsyncSessionLocal, is_db_available
                if not await is_db_available():
                    return 0
                async with AsyncSessionLocal() as db:
                    count = await self._do_hydrate(db)
            else:
                count = await self._do_hydrate(db_session)
            
            self._hydrated = True
            return count
        except Exception:
            return 0

    async def _do_hydrate(self, db) -> int:
        from db.repair_repository import RepairIncidentRepo
        from repair.schemas.incident import IncidentSource, IncidentSeverity, IncidentRecord
        
        records = await RepairIncidentRepo.get_open(db, limit=500)
        loaded = 0
        for rec in records:
            try:
                fp = self._fingerprint(rec.symptom, rec.module)
                if fp not in self._seen:
                    # DB'den gelen inci Schema'ya çevir
                    inc = IncidentRecord(
                        incident_id=rec.incident_id,
                        source=IncidentSource(rec.source),
                        severity=IncidentSeverity(rec.severity),
                        service=rec.service,
                        module=rec.module,
                        symptom=rec.symptom,
                        stack_trace=rec.stack_trace,
                        suspected_files=rec.suspected_files or [],
                        failing_tests=rec.failing_tests or [],
                        reproduction_hint=rec.reproduction_hint or "",
                        context=rec.context_data or {},
                        occurrence_count=rec.occurrence_count,
                        status=rec.status,
                        first_seen_at=rec.first_seen_at,
                        last_seen_at=rec.last_seen_at,
                    )
                    self._seen[fp] = inc
                    loaded += 1
            except ValueError:
                continue
        return loaded


# Singleton
incident_ingestor = IncidentIngestor()
