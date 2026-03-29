"""
Lessons Store — Faz 11

İnsan reviewer geri bildirimlerini saklar.
Root cause ranker ve patch planner'a öğrenme girdisi sağlar.

Feedback kodları:
  wrong_root_cause    — yanlış kök neden seçildi
  too_broad_patch     — çok geniş değişiklik
  insufficient_tests  — yeterli test yok
  risky_change        — riskli değişiklik
  wrong_target_file   — yanlış dosya hedeflendi
  correct_fix         — doğru düzeltme
"""
from __future__ import annotations

import uuid
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

from observability.logging import get_logger

_log = get_logger("repair.memory.lessons")


FEEDBACK_CODES = [
    "wrong_root_cause",
    "too_broad_patch",
    "insufficient_tests",
    "risky_change",
    "wrong_target_file",
    "correct_fix",
    "other",
]


@dataclass
class FeedbackRecord:
    """Bir insan kararından gelen yapılandırılmış geri bildirim."""
    feedback_id:     str
    job_id:          str
    pr_id:           str
    decided_by:      str
    decision:        str           # "approved" | "rejected" | "merged"
    feedback_code:   str           # FEEDBACK_CODES içinden
    feedback_note:   str           = ""
    module:          str           = ""
    incident_class:  str           = ""
    hypothesis_used: str           = ""
    recorded_at:     datetime      = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "feedback_id":     self.feedback_id,
            "job_id":          self.job_id,
            "pr_id":           self.pr_id,
            "decided_by":      self.decided_by,
            "decision":        self.decision,
            "feedback_code":   self.feedback_code,
            "feedback_note":   self.feedback_note,
            "module":          self.module,
            "incident_class":  self.incident_class,
            "hypothesis_used": self.hypothesis_used,
            "recorded_at":     self.recorded_at.isoformat(),
        }


class LessonsStore:
    """
    Tüm feedback kayıtlarını depolar.
    Öğrenme modüllerine aggregate veri sağlar.
    """

    def __init__(self):
        self._records: list[FeedbackRecord] = []

    def record(
        self,
        job_id:          str,
        pr_id:           str,
        decided_by:      str,
        decision:        str,
        feedback_code:   str,
        feedback_note:   str  = "",
        module:          str  = "",
        incident_class:  str  = "",
        hypothesis_used: str  = "",
    ) -> FeedbackRecord:
        rec = FeedbackRecord(
            feedback_id    = f"fb_{uuid.uuid4().hex[:8]}",
            job_id         = job_id,
            pr_id          = pr_id,
            decided_by     = decided_by,
            decision       = decision,
            feedback_code  = feedback_code if feedback_code in FEEDBACK_CODES else "other",
            feedback_note  = feedback_note,
            module         = module,
            incident_class = incident_class,
            hypothesis_used= hypothesis_used,
        )
        self._records.append(rec)
        _log.info(
            f"Feedback kaydedildi: {rec.feedback_id} "
            f"decision={decision} code={feedback_code} module={module}"
        )

        # Root cause ranker'a öğret
        self._teach_ranker(rec)
        return rec

    def _teach_ranker(self, rec: FeedbackRecord) -> None:
        """Feedback'i root cause ranker'a ilet."""
        try:
            from repair.analysis.root_cause_ranker import get_root_cause_ranker
            ranker = get_root_cause_ranker()
            outcome = "success" if rec.decision in ("approved", "merged") else "rejected"
            ranker.record_lesson(
                problem_class       = rec.incident_class,
                module              = rec.module,
                accepted_hypothesis = rec.hypothesis_used,
                outcome             = outcome,
                feedback_code       = rec.feedback_code,
            )
            
            # Faz 12.1: Puanla ve Playbook / Guardrail Üret
            if rec.decision in ("approved", "merged") and rec.feedback_note:
                from memory.store import memory_store
                import asyncio
                from db.session import AsyncSessionLocal
                
                async def _save_async():
                    async with AsyncSessionLocal() as db:
                        await memory_store.save_playbook(
                            db=db,
                            module=rec.module,
                            note=rec.feedback_note,
                            hypothesis=rec.hypothesis_used
                        )
                
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(_save_async())
                except RuntimeError:
                    pass
        except Exception as e:
            _log.debug(f"Ranker öğretme hatası (ignore): {e}")

    def get_by_job(self, job_id: str) -> list[FeedbackRecord]:
        return [r for r in self._records if r.job_id == job_id]

    def rejection_reasons(self, last_n: int = 100) -> dict:
        recent = self._records[-last_n:]
        codes  = [r.feedback_code for r in recent if r.decision == "rejected"]
        return dict(Counter(codes).most_common())

    def module_feedback_summary(self, module: str) -> dict:
        recs = [r for r in self._records if r.module == module]
        if not recs:
            return {"module": module, "total": 0}
        total    = len(recs)
        approved = sum(1 for r in recs if r.decision in ("approved", "merged"))
        rejected = sum(1 for r in recs if r.decision == "rejected")
        codes    = Counter(r.feedback_code for r in recs if r.decision == "rejected")
        return {
            "module":          module,
            "total":           total,
            "approved":        approved,
            "rejected":        rejected,
            "approval_rate":   round(approved / total * 100, 1),
            "top_reject_codes": dict(codes.most_common(3)),
        }

    def list_recent(self, limit: int = 20) -> list[dict]:
        return [r.to_dict() for r in reversed(self._records[-limit:])]

    def stats(self) -> dict:
        total    = len(self._records)
        approved = sum(1 for r in self._records if r.decision in ("approved", "merged"))
        rejected = sum(1 for r in self._records if r.decision == "rejected")
        return {
            "total_feedback":    total,
            "approved":          approved,
            "rejected":          rejected,
            "approval_rate":     round(approved / total * 100, 1) if total else 0.0,
            "top_reject_reasons": self.rejection_reasons(50),
        }


_lessons_store = LessonsStore()


def get_lessons_store() -> LessonsStore:
    return _lessons_store
