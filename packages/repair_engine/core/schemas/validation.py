"""
ValidationReport — Patch doğrulama sonucu.

Faz 10.1:
  - reproducer_defined, reproducer_passed_before_patch, reproducer_passed_after_patch
  - patch_apply_output, verification_gaps alanları eklendi.
  - overall_passed() artık reproducer + apply durumunu da değerlendiriyor.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class ValidationStatus(str, Enum):
    PASSED  = "passed"
    FAILED  = "failed"
    PARTIAL = "partial"
    SKIPPED = "skipped"


@dataclass
class ValidationReport:
    validation_id:        str
    patch_plan_id:        str

    # ── Temel doğrulama kapıları ──────────────────────────
    bug_reproduced:       bool             = False
    patch_applied:        bool             = False
    syntax_ok:            bool             = False
    lint_ok:              bool             = False
    typecheck_ok:         bool             = False
    unit_tests_ok:        bool             = False
    integration_tests_ok: bool             = False
    smoke_ok:             bool             = False
    security_ok:          bool             = False
    architecture_ok:      bool             = False

    # ── Reproducer zinciri (Faz 10.1) ────────────────────
    # Reproducer test planında tanımlı mı?
    reproducer_defined:                bool          = False
    # Patch uygulanmadan önce reproducer FAIL etti mi? (beklenen)
    reproducer_passed_before_patch:    Optional[bool] = None
    # Patch uygulandıktan sonra reproducer PASS etti mi? (beklenen)
    reproducer_passed_after_patch:     Optional[bool] = None

    # ── Patch uygulama çıktısı (Faz 10.1) ────────────────
    patch_apply_output:   str             = ""

    # ── Eksiklik listesi (Faz 10.1) ──────────────────────
    # "reproducer yok", "test tanımlanmadı", "sandbox binary eksik" vb.
    verification_gaps:    list[str]       = field(default_factory=list)

    # ── Risk & sonuç ─────────────────────────────────────
    regression_risk:      str             = "unknown"   # low|medium|high
    security_risk:        str             = "unknown"
    confidence:           int             = 0           # 0-100
    notes:                list[str]       = field(default_factory=list)
    test_output:          str             = ""
    final_status:         ValidationStatus = ValidationStatus.SKIPPED
    final_recommendation: str             = "manual_review_only"
    verified_at:          datetime        = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @classmethod
    def create(cls, patch_plan_id: str, **kwargs) -> "ValidationReport":
        return cls(
            validation_id=f"val_{uuid.uuid4().hex[:8]}",
            patch_plan_id=patch_plan_id,
            **kwargs,
        )

    def overall_passed(self) -> bool:
        """
        Tüm kritik kapılar geçildi mi?
        - Syntax, security, architecture, patch_applied, unit_tests zorunlu.
        - Reproducer tanımlıysa tam kanıt zinciri zorunlu:
            * patch öncesi FAIL (bug gerçekten vardı)
            * patch sonrası PASS (bug düzeltildi)
          Her iki koşul da sağlanmazsa overall_passed=False.
          Bu kural, "reproducer zaten geçiyordu, bug yoktu" senaryosunu engeller.

        Faz 10.1: reproducer_passed_before_patch=True ise bug yoktu demek —
        create_pr seviyesine çıkılmaz.
        """
        core_gates = (
            self.syntax_ok
            and self.lint_ok
            and self.unit_tests_ok
            and self.security_ok
            and self.architecture_ok
            and self.patch_applied
        )
        if not core_gates:
            return False
        # Reproducer tanımlıysa tam kanıt zinciri zorunlu
        if self.reproducer_defined:
            # Patch öncesi FAIL bekliyoruz (bug gerçekten yeniden üretildi)
            if self.reproducer_passed_before_patch is not False:
                return False   # Öncesi geçtiyse bug yoktu — kanıt eksik
            # Patch sonrası PASS bekliyoruz (düzeltildi)
            if self.reproducer_passed_after_patch is not True:
                return False
        return True

    def reproducer_evidence_ok(self) -> bool:
        """
        Reproducer kanıt zinciri tam mı?
        Gerekli koşullar:
          1. Reproducer tanımlı olmalı
          2. Patch öncesi FAIL (bug gerçekten yeniden üretildi)
          3. Patch sonrası PASS (düzeltme çalıştı)
        """
        if not self.reproducer_defined:
            return False
        return (
            self.reproducer_passed_before_patch is False   # Bug önce VARDI
            and self.reproducer_passed_after_patch is True  # Patch sonrası GEÇTİ
        )

    def to_dict(self) -> dict:
        return {
            "validation_id":                  self.validation_id,
            "patch_plan_id":                  self.patch_plan_id,
            "bug_reproduced":                 self.bug_reproduced,
            "patch_applied":                  self.patch_applied,
            "patch_apply_output":             self.patch_apply_output[:500],
            "syntax_ok":                      self.syntax_ok,
            "lint_ok":                        self.lint_ok,
            "typecheck_ok":                   self.typecheck_ok,
            "unit_tests_ok":                  self.unit_tests_ok,
            "integration_tests_ok":           self.integration_tests_ok,
            "smoke_ok":                       self.smoke_ok,
            "security_ok":                    self.security_ok,
            "architecture_ok":                self.architecture_ok,
            "reproducer_defined":             self.reproducer_defined,
            "reproducer_passed_before_patch": self.reproducer_passed_before_patch,
            "reproducer_passed_after_patch":  self.reproducer_passed_after_patch,
            "reproducer_evidence_ok":         self.reproducer_evidence_ok(),
            "verification_gaps":              self.verification_gaps,
            "regression_risk":                self.regression_risk,
            "security_risk":                  self.security_risk,
            "confidence":                     self.confidence,
            "notes":                          self.notes,
            "final_status":                   self.final_status.value,
            "final_recommendation":           self.final_recommendation,
            "overall_passed":                 self.overall_passed(),
            "verified_at":                    self.verified_at.isoformat(),
        }
