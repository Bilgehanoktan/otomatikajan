"""
Incident Memory — Operational Memory Layer
Geçmiş incident'leri, pattern'leri ve tekrar eden hataları saklar.

Hafıza iki seviyede çalışır:
1. In-memory (hızlı erişim, process içi)
2. DB kalıcı (RepairIncidentRecord tablosu)
"""

import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, List

from repair.schemas.incident import IncidentRecord, IncidentSeverity
from observability.logging import get_logger

_log = get_logger("repair.memory.incident")


@dataclass
class IncidentPattern:
    """Tekrar eden incident örüntüsü."""
    module:         str
    symptom_prefix: str
    count:          int
    severities:     list[str]
    first_seen:     str
    last_seen:      str
    resolved_count: int = 0

    @property
    def resolution_rate(self) -> float:
        if self.count == 0:
            return 0.0
        return round(self.resolved_count / self.count, 2)


@dataclass
class ModuleHealthProfile:
    """Modül bazlı sağlık istatistikleri."""
    module:          str
    total_incidents: int = 0
    open_incidents:  int = 0
    resolved:        int = 0
    avg_severity:    str = "low"
    last_incident:   Optional[str] = None
    hotspot_score:   float = 0.0   # 0-1, 1 = en sık bozulan


class IncidentMemory:
    """
    Tüm incident geçmişini tutar.
    Pattern tespiti, hotspot analizi, tekrar oranı sağlar.
    """

    MAX_INCIDENTS = 1000   # bellek limiti

    def __init__(self):
        self._incidents:       dict[str, IncidentRecord] = {}
        self._by_module:       defaultdict[str, list[str]] = defaultdict(list)
        self._severity_counts: Counter = Counter()
        self._resolution_times: list[float] = []   # saniye cinsinden
        self._hydrated = False

    # ── Yazma ──────────────────────────────────────────────
    def record(self, incident: IncidentRecord) -> None:
        """Yeni incident kaydet."""
        if len(self._incidents) >= self.MAX_INCIDENTS:
            # En eski open incident'i temizle
            oldest = min(
                (i for i in self._incidents.values() if i.status.lower() == "open"),
                key=lambda i: i.first_seen_at,
                default=None,
            )
            if oldest:
                del self._incidents[oldest.incident_id]

        self._incidents[incident.incident_id] = incident
        self._by_module[incident.module].append(incident.incident_id)
        self._severity_counts[incident.severity.value] += 1
        _log.info(f"Incident kaydedildi: {incident.incident_id} ({incident.module})")

    def mark_resolved(self, incident_id: str, duration_s: float = 0.0) -> bool:
        """Incident'i çözümlendi olarak işaretle."""
        inc = self._incidents.get(incident_id)
        if not inc:
            return False
        inc.status = "resolved"
        if duration_s > 0:
            self._resolution_times.append(duration_s)
        return True

    def mark_rejected(self, incident_id: str) -> bool:
        """Incident'i reddedildi olarak işaretle."""
        inc = self._incidents.get(incident_id)
        if not inc:
            return False
        inc.status = "rejected"
        return True

    # ── Okuma ──────────────────────────────────────────────
    def get(self, incident_id: str) -> Optional[IncidentRecord]:
        return self._incidents.get(incident_id)

    def get_open(self) -> list[IncidentRecord]:
        return [i for i in self._incidents.values() if i.status.lower() == "open"]

    def get_by_module(self, module: str, limit: int = 20) -> list[IncidentRecord]:
        ids = self._by_module.get(module, [])[-limit:]
        return [self._incidents[i] for i in ids if i in self._incidents]

    def get_similar(self, symptom: str, module: str, limit: int = 5) -> list[IncidentRecord]:
        """Benzer semptomlara sahip geçmiş incident'leri bul."""
        symptom_lower = symptom.lower()[:50]
        results = []
        for inc in self._incidents.values():
            if inc.module == module and symptom_lower[:30] in inc.symptom.lower():
                results.append(inc)
        return sorted(results, key=lambda i: i.last_seen_at, reverse=True)[:limit]

    # ── Analiz ─────────────────────────────────────────────
    def hotspot_modules(self, top_n: int = 5) -> list[ModuleHealthProfile]:
        """En sık bozulan modülleri döner."""
        module_counts = {
            module: len(ids)
            for module, ids in self._by_module.items()
        }
        total = sum(module_counts.values()) or 1
        profiles = []
        for module, count in sorted(module_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]:
            incidents = self.get_by_module(module)
            resolved  = sum(1 for i in incidents if i.status == "resolved")
            sev_counts = Counter(i.severity.value for i in incidents)
            dominant_sev = sev_counts.most_common(1)[0][0] if sev_counts else "low"
            last = max((i.last_seen_at for i in incidents), default=None)
            profiles.append(ModuleHealthProfile(
                module=module,
                total_incidents=count,
                open_incidents=sum(1 for i in incidents if i.status.lower() == "open"),
                resolved=resolved,
                avg_severity=dominant_sev,
                last_incident=last.isoformat() if last else None,
                hotspot_score=round(count / total, 3),
            ))
        return profiles

    def detect_patterns(self) -> list[IncidentPattern]:
        """Tekrar eden örüntüleri tespit et."""
        symptom_groups: defaultdict[str, list[IncidentRecord]] = defaultdict(list)
        for inc in self._incidents.values():
            key = f"{inc.module}::{inc.symptom[:40]}"
            symptom_groups[key].append(inc)

        patterns = []
        for key, group in symptom_groups.items():
            if len(group) < 2:
                continue
            module, symptom_prefix = key.split("::", 1)
            severities = [i.severity.value for i in group]
            resolved = sum(1 for i in group if i.status == "resolved")
            first = min(i.first_seen_at for i in group)
            last  = max(i.last_seen_at  for i in group)
            patterns.append(IncidentPattern(
                module=module,
                symptom_prefix=symptom_prefix,
                count=len(group),
                severities=severities,
                first_seen=first.isoformat(),
                last_seen=last.isoformat(),
                resolved_count=resolved,
            ))
        return sorted(patterns, key=lambda p: p.count, reverse=True)

    def mean_time_to_resolve(self) -> float:
        """Ortalama çözüm süresi (saniye)."""
        if not self._resolution_times:
            return 0.0
        return round(sum(self._resolution_times) / len(self._resolution_times), 1)

    def stats(self) -> dict:
        open_c    = sum(1 for i in self._incidents.values() if i.status.lower() == "open")
        resolved_c = sum(1 for i in self._incidents.values() if i.status.lower() == "resolved")
        return {
            "total":           len(self._incidents),
            "open":            open_c,
            "resolved":        resolved_c,
            "rejected":        len(self._incidents) - open_c - resolved_c,
            "severity_counts": dict(self._severity_counts),
            "mean_time_to_resolve_s": self.mean_time_to_resolve(),
            "hotspot_modules": [
                {"module": p.module, "count": p.total_incidents, "score": p.hotspot_score}
                for p in self.hotspot_modules(3)
            ],
            "is_hydrated": self._hydrated,
        }

    async def hydrate_from_db(self, db_session=None) -> int:
        """
        Veritabanındaki açık (open) olayları belleğe yükle.
        Sistem başlangıcında (lifespan) çağrılmalıdır.
        """
        if self._hydrated:
            return 0

        _log.info("IncidentMemory: Veritabanından geri yükleme (hydration) başlatılıyor...")
        count = 0
        try:
            if not db_session:
                from db.session import AsyncSessionLocal, is_db_available
                if not await is_db_available():
                    _log.warning("Hydration atlandı: DB hazır değil.")
                    return 0
                
                async with AsyncSessionLocal() as db:
                    count = await self._do_hydrate(db)
            else:
                count = await self._do_hydrate(db_session)
                
            self._hydrated = True
            _log.info(f"IncidentMemory: {count} olay geri yüklendi.")
            return count
        except Exception as e:
            _log.error(f"Hydration hatası: {e}")
            return 0

    async def _do_hydrate(self, db) -> int:
        from db.repair_repository import RepairIncidentRepo
        from repair.schemas.incident import IncidentSource, IncidentSeverity
        
        # Sadece 'open' olanları belleğe al
        records = await RepairIncidentRepo.get_open(db, limit=self.MAX_INCIDENTS)
        count = 0
        for rec in records:
            try:
                # DB modelini Schema nesnesine dönüştür
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
                self.record(inc)
                count += 1
            except ValueError as ve:
                _log.warning(f"Hydration: Geçersiz kayıt atlandı ({rec.incident_id}): {ve}")
                continue
        return count


# Singleton
incident_memory = IncidentMemory()
