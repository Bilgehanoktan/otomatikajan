"""
Patch Planner
DiagnosisTicket -> PatchPlan

KOD YAZMAZ. Sadece plan üretir.
Kural: büyük refactor yasak, sadece minimal hedefli değişiklik.
"""

import os
from typing import Optional

from packages.repair_engine.schemas.diagnosis import DiagnosisTicket, ProblemClass, RepairMode
from packages.repair_engine.schemas.patch_plan import PatchPlan, PatchAction, ChangeType, RiskLevel
from packages.observability.logging import get_logger

_log = get_logger("repair.patch_planner")

# ── Güvenli Hedef Dosya Whitelist ─────────────────────────────
# Sadece bu dosyalara otomatik patch üretilebilir
SAFE_PATCH_TARGETS = {
    "main.py",
    "config.py",
    "core/orchestrator.py",
    "core/job_queue.py",
    "api/routes.py",
    "api/task_router.py",
    "api/task_read_router.py",
    "api/task_write_router.py",
    "api/task_control_router.py",
    "llm/model_orchestrator.py",
    "heal/taxonomy.py",
    "heal/recovery_strategies.py",
    "agents/agent_registry.py",
}

# ── Manuel Review Gerektiren Dosyalar ─────────────────────────
MANUAL_REVIEW_TARGETS = {
    "auth/jwt_auth.py",
    "db/models.py",
    "alembic/versions/",
    "docker-compose.yml",
    "Dockerfile",
}

# ── Problem Sınıfı -> Tipik Değişiklik Matrisi ─────────────────
_CLASS_TO_ACTIONS: dict[ProblemClass, list[tuple[ChangeType, str]]] = {
    ProblemClass.IMPORT_ERROR: [
        (ChangeType.ADD_IMPORT, "Eksik import ifadesi ekle"),
    ],
    ProblemClass.NULL_STATE_ERROR: [
        (ChangeType.ADD_NULL_CHECK, "None kontrolü ekle veya varsayılan değer ver"),
    ],
    ProblemClass.INTERFACE_MISMATCH: [
        (ChangeType.FIX_RETURN_TYPE, "Dönüş tipi veya parametre tipi düzelt"),
        (ChangeType.FIX_CONTRACT, "Kontrat uyumunu sağla"),
    ],
    ProblemClass.SCHEMA_MISMATCH: [
        (ChangeType.FIX_CONTRACT, "Schema / Pydantic model uyumunu sağla"),
    ],
    ProblemClass.CONTRACT_BROKEN: [
        (ChangeType.FIX_CONTRACT, "Public sözleşme bozuksa minimal düzeltme uygula"),
    ],
    ProblemClass.ROUTE_ERROR: [
        (ChangeType.FIX_SYMBOL, "Router veya endpoint tanımını düzelt"),
    ],
    ProblemClass.CONFIG_ERROR: [
        (ChangeType.CONFIG_REPAIR, "Config değeri veya env okuma düzelt"),
    ],
    ProblemClass.QUEUE_FAILURE: [
        (ChangeType.ADD_ERROR_HANDLER, "Queue hata işleme ekle"),
    ],
}


class PatchPlanner:
    """
    Ticket'ten minimal PatchPlan üretir.
    Kod üretmez — sadece ne yapılacağını planlar.
    """

    def plan(
        self,
        ticket: DiagnosisTicket,
        project_root: str = ".",
    ) -> Optional[PatchPlan]:
        """
        Plan üret. Güvenli değilse None döner.
        """
        # Manuel modda plan üretme
        if ticket.recommended_mode == RepairMode.MANUAL_ONLY:
            _log.info(f"Ticket {ticket.ticket_id}: manuel review modu, plan atlandı.")
            return None

        # Seçilmiş hipotez yoksa planlanamaz
        if not ticket.selected_hypothesis:
            _log.warning(f"Ticket {ticket.ticket_id}: seçilmiş hipotez yok.")
            return None

        # Güvenli hedef dosyaları filtrele
        safe_files = self._filter_safe_files(ticket.candidate_files, project_root)
        if not safe_files:
            _log.warning(f"Ticket {ticket.ticket_id}: güvenli patch hedefi yok.")
            return None

        actions = self._build_actions(ticket.classification, safe_files)
        risk    = self._assess_risk(ticket, safe_files)
        tests   = self._suggest_tests(ticket)

        plan = PatchPlan.create(
            ticket_id=ticket.ticket_id,
            target_files=safe_files,
            actions=actions,
            risk=risk,
            required_tests=tests,
            rollback_strategy=f"git revert veya {safe_files[0]} önceki sürümüne geri dön.",
            rationale=(
                f"Kök neden: {ticket.selected_hypothesis.title} "
                f"(güven: {ticket.selected_hypothesis.confidence}%). "
                f"Minimal hedefli {ticket.classification.value} düzeltmesi."
            ),
            approved=risk == RiskLevel.LOW,  # Düşük risk -> otomatik onay
        )
        return plan

    def _filter_safe_files(self, candidate_files: list[str], project_root: str) -> list[str]:
        """
        Sadece whitelist'teki dosyalara izin ver.
        Whitelist dışındaki dosyalar, fiziksel olarak var olsa bile reddedilir.
        P0 güvenlik düzeltmesi — bu kuralın delinmesi yasaktır.
        """
        result = []
        for f in candidate_files:
            f_norm = f.replace("\\", "/")
            # 1. Manuel review hedeflerini kesinlikle dışla
            if any(f_norm.startswith(m.replace("\\", "/")) for m in MANUAL_REVIEW_TARGETS):
                _log.info(f"Patch hedefi dışlandı (manual review zorunlu): {f}")
                continue
            # 2. Sadece whitelist içindeyse kabul et
            if f_norm in SAFE_PATCH_TARGETS:
                result.append(f_norm)
                continue
            # 3. Whitelist dışı -> kesinlikle reddet (dosya varlığı kriter değil)
            _log.debug(f"Whitelist dışı hedef reddedildi (güvenlik): {f}")

        if len(result) < len(candidate_files):
            rejected = [f for f in candidate_files if f.replace("\\", "/") not in result]
            if rejected:
                _log.info(f"Whitelist filtresi: {len(rejected)} dosya reddedildi — {rejected[:3]}")

        return result[:3]   # maksimum 3 dosya

    def _build_actions(self, cls: ProblemClass, files: list[str]) -> list[PatchAction]:
        action_templates = _CLASS_TO_ACTIONS.get(cls, [
            (ChangeType.UNKNOWN, "Belirsiz değişiklik — manuel inceleme gerekli"),
        ])
        actions = []
        for change_type, description in action_templates:
            for f in files:
                actions.append(PatchAction(
                    file=f,
                    symbol=None,
                    change_type=change_type,
                    description=description,
                ))
        return actions

    def _assess_risk(self, ticket: DiagnosisTicket, files: list[str]) -> RiskLevel:
        if ticket.severity in ("critical", "high"):
            return RiskLevel.MEDIUM
        if len(files) > 2:
            return RiskLevel.MEDIUM
        if ticket.classification in (
            ProblemClass.IMPORT_ERROR,
            ProblemClass.NULL_STATE_ERROR,
            ProblemClass.CONFIG_ERROR,
        ):
            return RiskLevel.LOW
        return RiskLevel.MEDIUM

    def _suggest_tests(self, ticket: DiagnosisTicket) -> list[str]:
        tests = list(ticket.failing_tests) if hasattr(ticket, "failing_tests") else []
        class_tests: dict[ProblemClass, list[str]] = {
            ProblemClass.IMPORT_ERROR:     ["tests/test_faz4.py"],
            ProblemClass.NULL_STATE_ERROR: ["tests/test_faz6.py"],
            ProblemClass.QUEUE_FAILURE:    ["tests/test_faz7.py"],
            ProblemClass.CONTRACT_BROKEN:  ["tests/test_faz7.py"],
        }
        for t in class_tests.get(ticket.classification, []):
            if t not in tests:
                tests.append(t)
        return tests


# Singleton
patch_planner = PatchPlanner()
