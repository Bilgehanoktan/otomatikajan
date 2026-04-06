"""
Root Cause Ranker — Faz 11

Hipotezleri öğrenme geçmişine göre sıralar.
Kural tabanlı scoring + geçmiş başarı oranı kombinasyonu.

Puanlama faktörleri:
  - Hata tipi + module eşleşmesi
  - Geçmiş benzer incident'lerde doğru çıkan hipotez kategorisi
  - Stack trace signal patternleri
  - Rejection geçmişi (yanlış hipotezleri düşür)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from packages.repair_engine.schemas.diagnosis import DiagnosisTicket, ProblemClass, RootCauseHypothesis
from packages.repair_engine.schemas.incident import IncidentRecord
from packages.observability.logging import get_logger

_log = get_logger("repair.analysis.ranker")


@dataclass
class HypothesisScore:
    hypothesis_id:   str
    hypothesis_title: str
    base_confidence: int
    rule_bonus:      int
    history_bonus:   int
    rejection_penalty: int
    final_score:     int
    reason:          str


@dataclass
class LessonRecord:
    """Geçmiş bir repair kararından öğrenilen ders."""
    problem_class:       str
    module:              str
    accepted_hypothesis: str   # başarılı olan hipotez türü
    outcome:             str   # "success" | "rejected" | "manual"
    feedback_code:       str   = ""  # "wrong_root_cause", "too_broad_patch", vb.
    recorded_at:         datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ── Kural tabanlı bonus ────────────────────────────────────────

_SIGNAL_RULES: list[tuple[str, str, int]] = [
    # (keyword_in_hypothesis, problem_class, bonus)
    ("import",    ProblemClass.IMPORT_ERROR.value,   +20),
    ("reference", ProblemClass.IMPORT_ERROR.value,   +15),
    ("route",     ProblemClass.ROUTE_ERROR.value,    +20),
    ("endpoint",  ProblemClass.ROUTE_ERROR.value,    +15),
    ("auth",      ProblemClass.AUTH_FAILURE.value,   +20),
    ("token",     ProblemClass.AUTH_FAILURE.value,   +15),
    ("queue",     ProblemClass.QUEUE_FAILURE.value,  +20),
    ("contract",  ProblemClass.CONTRACT_BROKEN.value,+20),
    ("schema",    ProblemClass.SCHEMA_MISMATCH.value,+20),
    ("config",    ProblemClass.CONFIG_ERROR.value,   +20),
]


def _rule_bonus(hypothesis: RootCauseHypothesis, problem_class: str) -> int:
    bonus = 0
    title_lower = hypothesis.title.lower() + hypothesis.description.lower()
    for kw, cls, pts in _SIGNAL_RULES:
        if kw in title_lower and cls == problem_class:
            bonus += pts
    return min(bonus, 35)   # maksimum kural bonusu


# ── Ranker ────────────────────────────────────────────────────

class RootCauseRanker:
    """
    Bir DiagnosisTicket içindeki hipotezleri yeniden sıralar.
    Geçmiş dersler + kural bonusleri birleştirilir.
    """

    def __init__(self):
        self._lessons:    list[LessonRecord] = []
        self._rejections: dict[str, int] = {}   # hypothesis pattern -> rejection count

    def rank(self, ticket: DiagnosisTicket, incident: IncidentRecord) -> DiagnosisTicket:
        """
        Ticket içindeki hypotheses listesini sırala ve selected_hypothesis güncelle.
        Orijinal ticket'ı değiştirmez; güncellenmiş kopyasını döndürür.
        """
        if not ticket.hypotheses:
            return ticket

        scores: list[HypothesisScore] = []
        for h in ticket.hypotheses:
            rb  = _rule_bonus(h, ticket.classification.value)
            hb  = self._history_bonus(h, ticket.classification.value, incident.module)
            rp  = self._rejection_penalty(h)
            final = max(0, min(100, h.confidence + rb + hb - rp))
            scores.append(HypothesisScore(
                hypothesis_id    = h.hypothesis_id,
                hypothesis_title = h.title,
                base_confidence  = h.confidence,
                rule_bonus       = rb,
                history_bonus    = hb,
                rejection_penalty= rp,
                final_score      = final,
                reason           = self._explain(rb, hb, rp),
            ))

        # Sırala
        scores.sort(key=lambda s: s.final_score, reverse=True)

        # Hipotez listesini yeniden düzenle
        score_map = {s.hypothesis_id: s.final_score for s in scores}
        ticket.hypotheses.sort(
            key=lambda h: score_map.get(h.hypothesis_id, h.confidence), reverse=True
        )

        # selected_hypothesis en yükseği
        if ticket.hypotheses:
            best = ticket.hypotheses[0]
            best.confidence = score_map.get(best.hypothesis_id, best.confidence)
            ticket.selected_hypothesis = best
            _log.debug(
                f"Ranker [{ticket.ticket_id}]: "
                f"'{best.title}' -> {best.confidence}% "
                f"(kural:{scores[0].rule_bonus} geçmiş:{scores[0].history_bonus})"
            )

        return ticket

    def record_lesson(
        self,
        problem_class:       str,
        module:              str,
        accepted_hypothesis: str,
        outcome:             str,
        feedback_code:       str = "",
    ) -> None:
        """Karar sonucu kaydet — gelecekteki ranking'e girdi sağlar."""
        lesson = LessonRecord(
            problem_class=problem_class,
            module=module,
            accepted_hypothesis=accepted_hypothesis,
            outcome=outcome,
            feedback_code=feedback_code,
        )
        self._lessons.append(lesson)

        # Rejection -> ceza artır
        if outcome == "rejected" and feedback_code == "wrong_root_cause":
            key = f"{problem_class}:{accepted_hypothesis[:40]}"
            self._rejections[key] = self._rejections.get(key, 0) + 1
            _log.info(f"Ranker: rejection kaydedildi — {key}")

    def _history_bonus(self, h: RootCauseHypothesis, problem_class: str, module: str) -> int:
        """Geçmişte bu tür hipotez başarılı çıkmışsa bonus ver."""
        bonus = 0
        h_lower = h.title.lower()
        for lesson in self._lessons:
            if lesson.outcome != "success":
                continue
            if lesson.problem_class == problem_class:
                if lesson.module == module:
                    bonus += 8
                elif lesson.accepted_hypothesis.lower() in h_lower:
                    bonus += 5
        return min(bonus, 25)

    def _rejection_penalty(self, h: RootCauseHypothesis) -> int:
        """Bu hipotez tipi daha önce reddedildiyse ceza uygula."""
        h_lower = h.title.lower()[:40]
        for key, count in self._rejections.items():
            if h_lower in key:
                return min(count * 10, 40)
        return 0

    def _explain(self, rb: int, hb: int, rp: int) -> str:
        parts = []
        if rb > 0:  parts.append(f"kural+{rb}")
        if hb > 0:  parts.append(f"geçmiş+{hb}")
        if rp > 0:  parts.append(f"red-{rp}")
        return ", ".join(parts) or "tarafsız"

    def stats(self) -> dict:
        return {
            "total_lessons":    len(self._lessons),
            "success_lessons":  sum(1 for l in self._lessons if l.outcome == "success"),
            "rejection_count":  sum(self._rejections.values()),
            "penalized_patterns": list(self._rejections.keys()),
        }


# Singleton
_ranker = RootCauseRanker()


def get_root_cause_ranker() -> RootCauseRanker:
    return _ranker
