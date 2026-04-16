"""
Policy Engine — Hangi kararın nerede otomasyon alabileceğini yönetir.

Karar seviyeleri:
  Level 0: sadece analiz raporu
  Level 1: otomatik branch + PR (ŞİMDİLİK MAKSİMUM SEVİYE)
  Level 2: düşük riskli otomatik merge (KAPALI)
  Level 3: production deploy (KAPALI)

Kural: İlk sürümde Level 1'den yukarı gidilmez.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from services.repair.schemas.diagnosis import DiagnosisTicket, ProblemClass, RepairMode
from services.repair.schemas.patch_plan import PatchPlan, RiskLevel
from services.repair.schemas.validation import ValidationReport
from services.observability.logging import get_logger

_log = get_logger("services.governance.policy.policy_engine")


class AutomationLevel(int, Enum):
    REPORT_ONLY = 0    # Sadece rapor
    CREATE_PR   = 1    # Branch + PR (maksimum izin)
    AUTO_MERGE  = 2    # Otomatik merge (KAPALI)
    AUTO_DEPLOY = 3    # Production deploy (KAPALI)


# Sistem genelinde maksimum izin verilen otomasyon seviyesi
SYSTEM_MAX_AUTOMATION = AutomationLevel.CREATE_PR


@dataclass
class PolicyDecision:
    allowed:              bool
    automation_level:     AutomationLevel
    requires_human:       bool
    blocking_reasons:     list[str]
    warnings:             list[str]
    recommended_action:   str    # "create_pr" | "manual_review_only" | "reject" | "report_only"

    def to_dict(self) -> dict:
        return {
            "allowed":            self.allowed,
            "automation_level":   self.automation_level.name,
            "requires_human":     self.requires_human,
            "blocking_reasons":   self.blocking_reasons,
            "warnings":           self.warnings,
            "recommended_action": self.recommended_action,
        }


# ── YASAKLI MODÜLLER ──────────────────────────────────────
# Bu modüllere otomatik patch KESİNLİKLE yasak
BLOCKED_MODULES = {
    "auth",
    "jwt_auth",
}

BLOCKED_FILE_PREFIXES = {
    "auth/",
    "alembic/",
}

# ── MANİPÜLASYON RİSKİ YÜKSEK DOSYALAR ──────────────────
HIGH_RISK_FILES = {
    "main.py",
    "db/models.py",
    "db/session.py",
    "core/orchestrator.py",
    "config.py",
}

# ── AUTO-PR İÇİN GEREKLİ KOŞULLAR ──────────────────────
# Hepsi True olmalı
AUTO_PR_REQUIRED_CONDITIONS = [
    "risk_level_low",
    "validation_passed",
    "security_ok",
    "architecture_ok",
    "not_blocked_module",
    "single_file_or_two_files",
    "has_required_tests",
    "confidence_above_60",
]


class PolicyEngine:
    """
    Repair job'ın hangi adımda ne kadar otomasyona sahip olabileceğine karar verir.
    Tüm kararlar kayıt altına alınır.
    """

    def __init__(self, max_automation: AutomationLevel = SYSTEM_MAX_AUTOMATION):
        self.max_automation = max_automation
        self._decisions: list[dict] = []

    def evaluate_patch(
        self,
        ticket:     DiagnosisTicket,
        plan:       PatchPlan,
        validation: ValidationReport,
        job_id:     str = "unknown",
    ) -> PolicyDecision:
        """
        Bir patch için tam policy değerlendirmesi.
        Karar: create_pr | manual_review_only | reject | report_only
        """
        blocking:  list[str] = []
        warnings:  list[str] = []

        # ── 1. Engellenen modüller ──────────────────────────
        for f in plan.target_files:
            module = f.split("/")[0]
            if module in BLOCKED_MODULES or any(f.startswith(p) for p in BLOCKED_FILE_PREFIXES):
                blocking.append(f"Engellenen modül: {f} (auth/alembic değiştirilemez)")

        # ── 2. Yüksek riskli dosyalar ──────────────────────
        for f in plan.target_files:
            if f in HIGH_RISK_FILES:
                warnings.append(f"Yüksek riskli dosya: {f} — ek dikkat gerekli")

        # ── 3. Validation durumu ────────────────────────────
        if not validation.syntax_ok:
            blocking.append("Syntax kontrolü başarısız")
        if not validation.security_ok:
            blocking.append("Güvenlik taraması başarısız")
        if not validation.architecture_ok:
            blocking.append("Mimari kontrol başarısız")

        # ── 4. Risk seviyesi ────────────────────────────────
        if plan.risk == RiskLevel.HIGH:
            blocking.append("Risk seviyesi HIGH — otomatik PR yasak")
        elif plan.risk == RiskLevel.MEDIUM:
            warnings.append("Risk seviyesi MEDIUM — insan incelemesi önerilir")

        # ── 5. Public API etkisi ────────────────────────────
        if plan.public_api_impact:
            blocking.append("Public API etkisi var — otomatik merge yasak")

        # ── 6. Migration ────────────────────────────────────
        if plan.migration_required:
            blocking.append("DB migration gerekiyor — insan onayı zorunlu")

        # ── 7. Validation confidence ─────────────────────────
        if validation.confidence < 60:
            warnings.append(f"Validation confidence düşük: {validation.confidence}%")
            if validation.confidence < 40:
                blocking.append("Validation confidence çok düşük (< 40%) — PR riskli")

        # ── 8. Çok dosya değişikliği ─────────────────────────
        if len(plan.target_files) > 3:
            warnings.append(f"Çok dosya değişiyor ({len(plan.target_files)}) — dikkatli ol")

        # ── 9. Ticket manuel mod ─────────────────────────────
        if ticket.recommended_mode == RepairMode.MANUAL_ONLY:
            blocking.append("Triage motoru manuel review önerdi")

        # ── Karar ───────────────────────────────────────────
        if blocking:
            level  = AutomationLevel.REPORT_ONLY
            action = "manual_review_only" if not any("syntax" in b or "security" in b for b in blocking) else "reject"
            allowed = False
        elif warnings and plan.risk == RiskLevel.MEDIUM:
            level   = AutomationLevel.REPORT_ONLY
            action  = "manual_review_only"
            allowed = False
        else:
            level   = AutomationLevel.CREATE_PR
            action  = "create_pr"
            allowed = True

        # Sistem maksimum sınırını aş
        level = min(level, self.max_automation)

        decision = PolicyDecision(
            allowed=allowed,
            automation_level=level,
            requires_human=not allowed or level < AutomationLevel.CREATE_PR,
            blocking_reasons=blocking,
            warnings=warnings,
            recommended_action=action,
        )

        # Kayıt
        self._decisions.append({
            "job_id":   job_id,
            "action":   action,
            "blocking": blocking,
            "warnings": warnings,
        })

        _log.info(
            f"Policy karar [{job_id}]: {action} "
            f"(blocking={len(blocking)}, warnings={len(warnings)})"
        )
        return decision

    def evaluate_triage(self, ticket: DiagnosisTicket) -> PolicyDecision:
        """Triage aşamasında erken policy kontrolü."""
        blocking: list[str] = []
        warnings: list[str] = []

        if ticket.classification in (ProblemClass.SECURITY_VIOLATION, ProblemClass.AUTH_FAILURE):
            blocking.append(f"Güvenlik sınıfı: {ticket.classification.value} — manuel review zorunlu")

        if ticket.severity in ("critical",):
            warnings.append("Critical severity — ekstra dikkat")

        allowed = len(blocking) == 0
        return PolicyDecision(
            allowed=allowed,
            automation_level=AutomationLevel.REPORT_ONLY if not allowed else AutomationLevel.CREATE_PR,
            requires_human=not allowed,
            blocking_reasons=blocking,
            warnings=warnings,
            recommended_action="manual_review_only" if not allowed else "continue",
        )

    def stats(self) -> dict:
        total   = len(self._decisions)
        blocked = sum(1 for d in self._decisions if d["blocking"])
        pr_ok   = sum(1 for d in self._decisions if d["action"] == "create_pr")
        manual  = sum(1 for d in self._decisions if d["action"] == "manual_review_only")
        return {
            "total_evaluated": total,
            "blocked":         blocked,
            "create_pr":       pr_ok,
            "manual_review":   manual,
            "block_rate":      round(blocked / total, 2) if total else 0.0,
        }


# Singleton
policy_engine = PolicyEngine()
