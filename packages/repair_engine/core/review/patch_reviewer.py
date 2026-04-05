"""
Patch Reviewer (İkinci Kapı)
GeneratedPatch -> ReviewDecision

Belgede tanımlanan Reviewer Agent:
"Patch'in gerçekten kök nedeni çözüp çözmediğini,
gereksiz değişiklik içerip içermediğini,
yeni risk üretip üretmediğini değerlendirir."

Kanıt zayıfsa reddet. Nezaketen onay verme.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from packages.repair_engine.generation.patch_generator import GeneratedPatch
from packages.repair_engine.schemas.patch_plan import PatchPlan
from packages.repair_engine.schemas.diagnosis import DiagnosisTicket
from packages.observability.logging import get_logger

_log = get_logger("repair.reviewer")


class ReviewDecisionType(str, Enum):
    APPROVE         = "approve"
    REVISE          = "revise"
    REJECT          = "reject"
    MANUAL_REVIEW   = "manual_review"


@dataclass
class ReviewReport:
    patch_relevance:    str              # patch semptomla ilgili mi?
    root_cause_aligned: bool             # kök neden ile mantıksal bağ var mı?
    unnecessary_changes: list[str]       # gereksiz değişiklik listesi
    regression_risk:    str              # low|medium|high
    security_risk:      str              # low|medium|high
    test_sufficient:    bool
    is_workaround:      bool             # geçici workaround mı?
    decision:           ReviewDecisionType
    notes:              list[str]        = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "patch_relevance":    self.patch_relevance,
            "root_cause_aligned": self.root_cause_aligned,
            "unnecessary_changes": self.unnecessary_changes,
            "regression_risk":    self.regression_risk,
            "security_risk":      self.security_risk,
            "test_sufficient":    self.test_sufficient,
            "is_workaround":      self.is_workaround,
            "decision":           self.decision.value,
            "notes":              self.notes,
        }


class PatchReviewer:
    """
    Kural tabanlı + opsiyonel LLM destekli patch incelemesi.
    """

    # Güvenlik riski içeren pattern'ler
    _SECURITY_PATTERNS = [
        r"\beval\s*\(",
        r"\bexec\s*\(",
        r"os\.system\s*\(",
        r"subprocess\.(call|run|Popen)\s*\(",
        r"shell\s*=\s*True",
        r"__import__\s*\(",
        r"open\s*\([^)]*['\"]w['\"]",  # write mode file open
        r"password\s*=\s*['\"][^'\"]+['\"]",
        r"secret\s*=\s*['\"][^'\"]+['\"]",
    ]

    # Gereksiz değişiklik göstergeleri
    _UNNECESSARY_PATTERNS = [
        (r"^\+.*#\s*(TODO|FIXME|HACK)", "TODO/FIXME yorum eklendi"),
        (r"^\+\s*print\s*\(", "print() eklendi — logger kullanılmalı"),
        (r"^\+.*import \*", "wildcard import eklendi"),
        (r"^\+.*pass\s*$", "bare pass eklendi — mantıksız"),
    ]

    def review(
        self,
        patch: GeneratedPatch,
        plan: PatchPlan,
        ticket: DiagnosisTicket,
    ) -> ReviewReport:
        notes:             list[str] = []
        unnecessary:       list[str] = []
        security_risk                = "low"
        regression_risk              = "low"

        # 1. Diff geçerli mi?
        if not patch.is_valid():
            return ReviewReport(
                patch_relevance="Diff geçersiz veya boş.",
                root_cause_aligned=False,
                unnecessary_changes=[],
                regression_risk="high",
                security_risk="low",
                test_sufficient=False,
                is_workaround=True,
                decision=ReviewDecisionType.REJECT,
                notes=["Boş veya geçersiz diff — patch reddedildi."],
            )

        # 2. Kök neden uyumu
        root_cause_aligned = False
        if ticket.selected_hypothesis:
            hyp_keywords = ticket.selected_hypothesis.title.lower().split()
            diff_lower = patch.diff.lower()
            matches = sum(1 for kw in hyp_keywords if kw in diff_lower)
            root_cause_aligned = matches >= 1
            if not root_cause_aligned:
                notes.append("Diff, seçilmiş kök neden hipoteziyle zayıf bağlantılı.")

        # 3. Güvenlik kontrolleri
        for pattern in self._SECURITY_PATTERNS:
            added_lines = [l for l in patch.diff.split("\n") if l.startswith("+")]
            added_text = "\n".join(added_lines)
            if re.search(pattern, added_text):
                security_risk = "high"
                notes.append(f"Güvenlik riski: {pattern} pattern'i eklenen kodda tespit edildi.")

        # 4. Gereksiz değişiklik kontrolü
        for pattern, label in self._UNNECESSARY_PATTERNS:
            if re.search(pattern, patch.diff, re.MULTILINE):
                unnecessary.append(label)
                notes.append(f"Gereksiz değişiklik: {label}")

        # 5. Diff boyutu kontrolü
        diff_lines = [l for l in patch.diff.split("\n") if l.startswith("+") or l.startswith("-")]
        if len(diff_lines) > 80:
            regression_risk = "medium"
            notes.append(f"Diff geniş: {len(diff_lines)} değişen satır — beklenenden fazla.")

        # 6. Test yeterliliği
        test_sufficient = len(plan.required_tests) > 0

        # 7. Geçici workaround tespiti
        is_workaround = any(
            kw in patch.diff.lower()
            for kw in ["# workaround", "# temp", "# hack", "# fixme", "# todo"]
        )

        # 8. Karar
        decision = self._decide(
            root_cause_aligned=root_cause_aligned,
            security_risk=security_risk,
            regression_risk=regression_risk,
            unnecessary=unnecessary,
            is_workaround=is_workaround,
            plan=plan,
        )

        return ReviewReport(
            patch_relevance=f"Diff {len(diff_lines)} satır. Kök neden bağı: {'var' if root_cause_aligned else 'zayıf'}.",
            root_cause_aligned=root_cause_aligned,
            unnecessary_changes=unnecessary,
            regression_risk=regression_risk,
            security_risk=security_risk,
            test_sufficient=test_sufficient,
            is_workaround=is_workaround,
            decision=decision,
            notes=notes,
        )

    def _decide(
        self,
        root_cause_aligned: bool,
        security_risk: str,
        regression_risk: str,
        unnecessary: list[str],
        is_workaround: bool,
        plan: PatchPlan,
    ) -> ReviewDecisionType:
        # Güvenlik riski -> her zaman manual
        if security_risk == "high":
            return ReviewDecisionType.MANUAL_REVIEW

        # Kök neden bağı yoksa -> revise
        if not root_cause_aligned:
            return ReviewDecisionType.REVISE

        # Yüksek regression riski -> manual
        if regression_risk == "high":
            return ReviewDecisionType.MANUAL_REVIEW

        # Çok gereksiz değişiklik -> revise
        if len(unnecessary) >= 2:
            return ReviewDecisionType.REVISE

        # Workaround + high risk -> reject
        if is_workaround and plan.risk.value in ("medium", "high"):
            return ReviewDecisionType.REJECT

        # Her şey geçtiyse approve
        return ReviewDecisionType.APPROVE


# Singleton
patch_reviewer = PatchReviewer()
