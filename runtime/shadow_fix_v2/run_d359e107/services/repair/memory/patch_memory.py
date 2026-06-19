"""
Patch Memory — Başarılı ve başarısız patch'lerin öğrenme deposu.

Tutulan bilgiler:
- Hangi patch başarılı oldu (kök neden sınıfı + hedef dosya)
- Hangi patch regresyon üretti
- Hangi diff pattern'leri güvenli
- Hangi dosyalar patch edildiğinde sorun çıkıyor
- Fix success rate per module
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from services.observability.logging import get_logger

_log = get_logger("repair.memory.patch")


class PatchOutcome(str, Enum):
    SUCCESS       = "success"
    REGRESSION    = "regression"
    REJECTED      = "rejected"
    MANUAL_MERGED = "manual_merged"
    ROLLED_BACK   = "rolled_back"


@dataclass
class PatchRecord:
    """Tek bir patch deneme kaydı."""
    record_id:       str
    job_id:          str
    incident_id:     str
    classification:  str         # ProblemClass değeri
    target_files:    list[str]
    diff_size_lines: int
    outcome:         PatchOutcome
    confidence:      int         # 0-100
    validation_score: int        # 0-100
    notes:           str         = ""
    recorded_at:     datetime    = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Lesson:
    """Birden fazla patch'den çıkarılan ders."""
    classification:  str
    target_files:    list[str]
    success_count:   int
    failure_count:   int
    common_pitfall:  str         # en sık başarısızlık nedeni
    recommended_approach: str

    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return round(self.success_count / total, 2) if total > 0 else 0.0


class PatchMemory:
    """
    Patch geçmişi ve öğrenme deposu.
    Gelecekteki patch planlarına rehberlik eder.
    """

    MAX_RECORDS = 500

    def __init__(self):
        self._records:        list[PatchRecord] = []
        self._by_class:       defaultdict[str, list[PatchRecord]] = defaultdict(list)
        self._by_file:        defaultdict[str, list[PatchRecord]] = defaultdict(list)
        self._danger_files:   set[str] = set()   # regresyon üreten dosyalar

    # ── Yazma ──────────────────────────────────────────────
    def record(
        self,
        job_id:          str,
        incident_id:     str,
        classification:  str,
        target_files:    list[str],
        diff_size_lines: int,
        outcome:         PatchOutcome,
        confidence:      int,
        validation_score: int,
        notes:           str = "",
    ) -> PatchRecord:
        import uuid
        rec = PatchRecord(
            record_id=f"prec_{uuid.uuid4().hex[:8]}",
            job_id=job_id,
            incident_id=incident_id,
            classification=classification,
            target_files=target_files,
            diff_size_lines=diff_size_lines,
            outcome=outcome,
            confidence=confidence,
            validation_score=validation_score,
            notes=notes,
        )

        if len(self._records) >= self.MAX_RECORDS:
            self._records.pop(0)

        self._records.append(rec)
        self._by_class[classification].append(rec)
        for f in target_files:
            self._by_file[f].append(rec)

        # Regresyon dosyalarını işaretle
        if outcome == PatchOutcome.REGRESSION:
            for f in target_files:
                self._danger_files.add(f)
                _log.warning(f"Regresyon tespit edildi: {f} -> danger_files'a eklendi")

        _log.info(f"Patch kaydedildi: {rec.record_id} — {outcome.value} ({classification})")
        return rec

    # ── Okuma / Sorgulama ───────────────────────────────────
    def success_rate_for(self, classification: str) -> float:
        """Belirli problem sınıfı için geçmiş başarı oranı."""
        records = self._by_class.get(classification, [])
        if not records:
            return 0.5   # Geçmiş yok -> belirsiz
        success = sum(1 for r in records if r.outcome in (PatchOutcome.SUCCESS, PatchOutcome.MANUAL_MERGED))
        return round(success / len(records), 2)

    def is_danger_file(self, filepath: str) -> bool:
        """Bu dosya geçmişte regresyon ürettiyse True."""
        return filepath in self._danger_files

    def get_lessons_for(self, classification: str) -> Optional[Lesson]:
        """Belirli sınıf için çıkarılmış ders."""
        records = self._by_class.get(classification, [])
        if len(records) < 3:
            return None

        success = [r for r in records if r.outcome in (PatchOutcome.SUCCESS, PatchOutcome.MANUAL_MERGED)]
        failure = [r for r in records if r.outcome in (PatchOutcome.REGRESSION, PatchOutcome.REJECTED)]

        # En sık başarısız olunan dosyayı bul
        fail_file_counts: Counter = defaultdict(int)
        from collections import Counter
        for r in failure:
            for f in r.target_files:
                fail_file_counts[f] += 1
        common_pitfall = (
            f"Sık regresyon dosyası: {max(fail_file_counts, key=fail_file_counts.get)}"
            if fail_file_counts else "Yeterli veri yok"
        )

        # Başarılı pattern
        success_files: Counter = defaultdict(int)
        for r in success:
            for f in r.target_files:
                success_files[f] += 1
        best_file = max(success_files, key=success_files.get) if success_files else "belirsiz"

        return Lesson(
            classification=classification,
            target_files=list(success_files.keys()),
            success_count=len(success),
            failure_count=len(failure),
            common_pitfall=common_pitfall,
            recommended_approach=f"Başarılı patch'ler genellikle {best_file} hedef aldı.",
        )

    def recent_failures(self, limit: int = 5) -> list[PatchRecord]:
        """Son başarısız patch'ler."""
        failures = [
            r for r in reversed(self._records)
            if r.outcome in (PatchOutcome.REGRESSION, PatchOutcome.REJECTED, PatchOutcome.ROLLED_BACK)
        ]
        return failures[:limit]

    def stats(self) -> dict:
        total    = len(self._records)
        success  = sum(1 for r in self._records if r.outcome in (PatchOutcome.SUCCESS, PatchOutcome.MANUAL_MERGED))
        fail     = sum(1 for r in self._records if r.outcome in (PatchOutcome.REGRESSION, PatchOutcome.REJECTED))
        rollback = sum(1 for r in self._records if r.outcome == PatchOutcome.ROLLED_BACK)

        by_class: dict[str, dict] = {}
        for cls, recs in self._by_class.items():
            s = sum(1 for r in recs if r.outcome in (PatchOutcome.SUCCESS, PatchOutcome.MANUAL_MERGED))
            by_class[cls] = {
                "total":        len(recs),
                "success":      s,
                "success_rate": round(s / len(recs), 2) if recs else 0.0,
            }

        return {
            "total":              total,
            "success":            success,
            "failed":             fail,
            "rolled_back":        rollback,
            "overall_success_rate": round(success / total, 2) if total else 0.0,
            "danger_files":       list(self._danger_files),
            "by_classification":  by_class,
        }


# Singleton
patch_memory = PatchMemory()
