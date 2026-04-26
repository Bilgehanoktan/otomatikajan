"""
Soft CEO — Approval Governor (Faz 2)

Bekleyen workflow'ları tarar, risk skoru üretir, aksiyon önerir.
Kör onay VERMEZ — düşük riskte öneri, orta riskte replay/repair,
yüksek riskte SOVEREIGN_PRIME veya quorum hattına eskale eder.

Her karar lineage zincirine mühürlenir.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from libs.db.models.core_models import (
    Project, ProjectStatus, SubTask,
    ApprovalRequest, OperationalIncident,
    SoftCeoDecisionType, SoftCeoRiskClass, PendingReason,
)
from libs.db.models.learning_models import ErrorFingerprint
from libs.db.models.repair_models import RepairIncident, RepairPatchLog
from libs.db.session import get_db_ctx
from services.governance.lineage_service import LineageService
from services.observability.logging import get_logger

logger = get_logger("governance.approval_governor")

# ── Configurable Thresholds ──────────────────────────────────
STALE_HOURS_WARNING = 2.0       # 2 saat sonra bayat sayılır
STALE_HOURS_CRITICAL = 24.0     # 24 saat sonra arşiv adayı
AUTO_APPROVE_MAX_RISK = 0.25    # Otomatik onay üst sınırı
REPLAY_MAX_RISK = 0.55          # Replay önerisi üst sınırı
MAX_RETRY_COUNT = 3             # Bu kadar denenmişse eskale et


# ── Case Data Object ─────────────────────────────────────────
@dataclass
class GovernorCase:
    """Soft CEO'nun bir iş kalemi hakkında topladığı bağlam."""
    project_id: str
    title: str
    status: str
    source: str
    priority: str

    # Workflow özeti
    total_steps: int = 0
    completed_steps: int = 0
    failed_steps: int = 0
    retry_count: int = 0
    error_detail: str = ""

    # İlişkili yönetişim verileri
    pending_approvals: List[Dict[str, Any]] = field(default_factory=list)
    open_incidents: List[Dict[str, Any]] = field(default_factory=list)
    active_fingerprints: List[Dict[str, Any]] = field(default_factory=list)
    repair_history: List[Dict[str, Any]] = field(default_factory=list)

    # Zamanlama
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    staleness_hours: float = 0.0

    # Hesaplanan değerler
    risk_score: float = 0.0
    risk_class: str = SoftCeoRiskClass.LOW.value
    pending_reason: str = PendingReason.PENDING_APPROVAL.value
    recommended_action: str = SoftCeoDecisionType.NO_ACTION.value
    rationale: str = ""
    requires_operator: bool = False


# ── Governor Ana Servisi ─────────────────────────────────────
class ApprovalGovernor:
    """
    Soft CEO üst denetim ajanı.

    Periyodik olarak çağrılır, bekleyen işleri tarar,
    her biri için bir Case oluşturur, risk skoru üretir,
    karar verir ve lineage'a yazar.
    """

    # ── 1. Tarama ─────────────────────────────────────────────
    async def scan_pending_items(self, db: Optional[AsyncSession] = None) -> List[GovernorCase]:
        """
        Sistemdeki bekleyen/hatalı/duraklatılmış tüm işleri tarar.
        Her biri için tam bir Case oluşturur, skorlar ve karar verir.
        """
        async def _run(session: AsyncSession) -> List[GovernorCase]:
            # Bekleyen statülerdeki projeleri bul
            stalled_statuses = [
                ProjectStatus.PENDING_APPROVAL,
                ProjectStatus.WAITING_APPROVAL,
                ProjectStatus.PAUSED,
                ProjectStatus.ERROR,
                ProjectStatus.FAILED,
                ProjectStatus.INTERRUPTED,
                ProjectStatus.PENDING_APPROVAL_AUTO,
            ]
            result = await session.execute(
                select(Project)
                .where(Project.status.in_(stalled_statuses))
                .order_by(Project.updated_at.asc())
                .limit(50)
            )
            projects = result.scalars().all()

            cases: List[GovernorCase] = []
            for project in projects:
                try:
                    case = await self.build_case(str(project.id), session)
                    self.score_case(case)
                    self.decide(case)
                    cases.append(case)
                except Exception as e:
                    logger.error(f"[Governor] Case build failed for {project.id}: {e}")

            logger.info(f"[Governor] Scanned {len(projects)} stalled items, built {len(cases)} cases.")
            return cases

        if db:
            return await _run(db)
        async with get_db_ctx() as session:
            return await _run(session)

    # ── 2. Case Oluşturma ─────────────────────────────────────
    async def build_case(self, project_id: str, db: AsyncSession) -> GovernorCase:
        """Bir proje için tüm ilişkili verileri toplar."""
        uid = uuid.UUID(project_id)
        now = datetime.now(timezone.utc)

        # Proje
        res = await db.execute(select(Project).where(Project.id == uid))
        project = res.scalar_one()

        p_status = project.status.value if hasattr(project.status, "value") else str(project.status)
        p_source = project.source.value if hasattr(project.source, "value") else str(project.source)
        p_priority = project.priority.value if hasattr(project.priority, "value") else str(project.priority)

        # Subtask istatistikleri
        step_res = await db.execute(
            select(
                func.count(SubTask.id).label("total"),
                func.count(SubTask.id).filter(SubTask.status == ProjectStatus.COMPLETED).label("done"),
                func.count(SubTask.id).filter(
                    SubTask.status.in_([ProjectStatus.ERROR, ProjectStatus.FAILED])
                ).label("failed"),
            ).where(SubTask.project_id == uid)
        )
        step_row = step_res.one()

        # İlişkili onay talepleri
        app_res = await db.execute(
            select(ApprovalRequest)
            .where(and_(ApprovalRequest.project_id == uid, ApprovalRequest.status == "pending"))
        )
        approvals = [
            {"id": str(a.id), "type": a.request_type, "reason": a.reason, "created_at": a.created_at}
            for a in app_res.scalars().all()
        ]

        # Açık operasyonel olaylar
        inc_res = await db.execute(
            select(OperationalIncident)
            .where(and_(
                OperationalIncident.project_id == uid,
                OperationalIncident.status.in_(["open", "investigating"])
            ))
        )
        incidents = [
            {"id": str(i.id), "type": i.incident_type, "severity": i.severity, "message": i.message}
            for i in inc_res.scalars().all()
        ]

        # Aktif hata parmak izleri (proje bağımsız, ama sistemik etkiyi gösterir)
        fp_res = await db.execute(
            select(ErrorFingerprint)
            .where(ErrorFingerprint.is_active == True)  # noqa: E712
            .order_by(ErrorFingerprint.recurrence_count.desc())
            .limit(5)
        )
        fingerprints = [
            {"id": str(f.id), "family": f.error_family, "service": f.service,
             "severity": f.severity, "count": f.recurrence_count}
            for f in fp_res.scalars().all()
        ]

        # Repair geçmişi
        repair_res = await db.execute(
            select(RepairPatchLog)
            .order_by(RepairPatchLog.recorded_at.desc())
            .limit(5)
        )
        repairs = [
            {"id": str(r.id), "outcome": r.outcome, "classification": r.classification}
            for r in repair_res.scalars().all()
        ]

        # Bayatlık hesapla
        ref_time = project.updated_at or project.created_at
        if ref_time:
            if ref_time.tzinfo is None:
                ref_time = ref_time.replace(tzinfo=timezone.utc)
            staleness = (now - ref_time).total_seconds() / 3600.0
        else:
            staleness = 0.0

        # Bekleme nedenini belirle
        pending_reason = self._classify_pending_reason(p_status, approvals, incidents)

        return GovernorCase(
            project_id=project_id,
            title=project.title,
            status=p_status,
            source=p_source,
            priority=p_priority,
            total_steps=step_row.total,
            completed_steps=step_row.done,
            failed_steps=step_row.failed,
            retry_count=project.retry_count or 0,
            error_detail=project.error_detail or "",
            pending_approvals=approvals,
            open_incidents=incidents,
            active_fingerprints=fingerprints,
            repair_history=repairs,
            created_at=project.created_at,
            updated_at=project.updated_at,
            staleness_hours=round(staleness, 2),
            pending_reason=pending_reason,
        )

    # ── 3. Risk Skorlama ──────────────────────────────────────
    def score_case(self, case: GovernorCase) -> None:
        """
        Deterministik risk skoru üretir (0.0 - 1.0).
        LLM çağırmaz, kurala dayalıdır.
        """
        score = 0.0

        # A) Bekleme süresi etkisi (max +0.25)
        if case.staleness_hours > STALE_HOURS_CRITICAL:
            score += 0.25
        elif case.staleness_hours > STALE_HOURS_WARNING:
            score += 0.10

        # B) Açık incident etkisi (max +0.30)
        for inc in case.open_incidents:
            sev = (inc.get("severity") or "medium").lower()
            if sev == "critical":
                score += 0.30
                break
            elif sev == "high":
                score += 0.20
            else:
                score += 0.05

        # C) Hata parmak izi yoğunluğu (max +0.15)
        for fp in case.active_fingerprints:
            if fp.get("count", 0) > 10:
                score += 0.15
                break
            elif fp.get("count", 0) > 3:
                score += 0.05

        # D) Retry sayısı etkisi (max +0.15)
        if case.retry_count >= MAX_RETRY_COUNT:
            score += 0.15
        elif case.retry_count > 0:
            score += 0.05

        # E) Başarısız adım oranı (max +0.15)
        if case.total_steps > 0:
            fail_ratio = case.failed_steps / case.total_steps
            score += min(fail_ratio * 0.30, 0.15)

        # F) Öncelik çarpanı
        if case.priority == "CRITICAL":
            score = min(score * 1.5, 1.0)
        elif case.priority == "HIGH":
            score = min(score * 1.2, 1.0)

        case.risk_score = round(min(score, 1.0), 3)

        # Risk sınıfı
        if case.risk_score >= 0.70:
            case.risk_class = SoftCeoRiskClass.CRITICAL.value
        elif case.risk_score >= 0.45:
            case.risk_class = SoftCeoRiskClass.HIGH.value
        elif case.risk_score >= 0.20:
            case.risk_class = SoftCeoRiskClass.MEDIUM.value
        else:
            case.risk_class = SoftCeoRiskClass.LOW.value

    # ── 4. Karar ──────────────────────────────────────────────
    def decide(self, case: GovernorCase) -> None:
        """
        Risk skoru ve bağlama göre aksiyon belirler.
        Kör onay VERMEZ — sadece öneri veya eskalasyon üretir.
        """
        D = SoftCeoDecisionType

        # Çürümüş iş → arşive
        if case.staleness_hours >= STALE_HOURS_CRITICAL and case.failed_steps > 0:
            case.recommended_action = D.ARCHIVE_STALE.value
            case.rationale = (
                f"İş {case.staleness_hours:.0f} saattir bekliyor ve {case.failed_steps} adım başarısız. "
                f"Aktif müdahale gelmediğinden arşive önerilir."
            )
            case.requires_operator = False
            return

        # CRITICAL risk → Quorum
        if case.risk_class == SoftCeoRiskClass.CRITICAL.value:
            case.recommended_action = D.REQUIRES_QUORUM.value
            case.rationale = (
                f"Risk skoru {case.risk_score:.2f} (CRITICAL). "
                f"Açık incident: {len(case.open_incidents)}, retry: {case.retry_count}. "
                f"Çoklu onay (quorum) gereklidir."
            )
            case.requires_operator = True
            return

        # HIGH risk → PRIME review
        if case.risk_class == SoftCeoRiskClass.HIGH.value:
            case.recommended_action = D.REQUIRES_PRIME_REVIEW.value
            case.rationale = (
                f"Risk skoru {case.risk_score:.2f} (HIGH). "
                f"SOVEREIGN_PRIME operatör incelemesi önerilir."
            )
            case.requires_operator = True
            return

        # Açık incident varken otomatik ilerleme yapılmaz
        if case.open_incidents:
            case.recommended_action = D.REQUIRES_HUMAN_CONTEXT.value
            case.rationale = (
                f"{len(case.open_incidents)} açık incident mevcut. "
                f"Otomatik ilerleme güvenli değil, operatör bağlamı gerekli."
            )
            case.requires_operator = True
            return

        # MEDIUM risk, hata var → replay öner
        if case.risk_class == SoftCeoRiskClass.MEDIUM.value:
            if case.failed_steps > 0 and case.retry_count < MAX_RETRY_COUNT:
                case.recommended_action = D.AUTO_REPLAY_CANDIDATE.value
                case.rationale = (
                    f"Orta risk ({case.risk_score:.2f}), {case.failed_steps} başarısız adım. "
                    f"Retry {case.retry_count}/{MAX_RETRY_COUNT}. Replay önerilebilir."
                )
                case.requires_operator = False
                return

        # LOW risk, sadece onay bekliyor → otomatik onay adayı
        if (case.risk_class == SoftCeoRiskClass.LOW.value
                and case.pending_reason == PendingReason.PENDING_APPROVAL.value
                and not case.open_incidents
                and case.risk_score <= AUTO_APPROVE_MAX_RISK):
            case.recommended_action = D.AUTO_APPROVE_CANDIDATE.value
            case.rationale = (
                f"Düşük risk ({case.risk_score:.2f}), açık incident yok, "
                f"onay bekleniyor. Otomatik onay adayı."
            )
            case.requires_operator = False
            return

        # Hiçbir kurala uymadı
        case.recommended_action = D.NO_ACTION.value
        case.rationale = "Mevcut durumda müdahale gerektiren bir koşul tespit edilmedi."
        case.requires_operator = False

    # ── 5. Uygulama ───────────────────────────────────────────
    async def execute(self, case: GovernorCase, db: Optional[AsyncSession] = None) -> Dict[str, Any]:
        """
        Karar sonucunu uygular.
        AUTO_APPROVE ve AUTO_REPLAY dışında hiçbir şeyi doğrudan yapmaz.
        Diğer her şey sadece lineage kaydı düşer.
        """
        action = case.recommended_action
        result = {"action": action, "executed": False, "project_id": case.project_id}

        if action == SoftCeoDecisionType.AUTO_APPROVE_CANDIDATE.value:
            result["executed"] = await self._execute_auto_approve(case, db)

        elif action == SoftCeoDecisionType.AUTO_REPLAY_CANDIDATE.value:
            result["executed"] = await self._execute_auto_replay(case, db)

        elif action == SoftCeoDecisionType.ARCHIVE_STALE.value:
            result["executed"] = await self._execute_archive(case, db)

        # Diğer kararlar (REQUIRES_PRIME_REVIEW, REQUIRES_QUORUM, vb.)
        # sadece lineage kaydı düşer, operatörü bekler.

        # Her durumda lineage kaydı düş
        await self.emit_lineage(case, db)

        logger.info(
            f"[Governor] {case.project_id}: {action} "
            f"(risk={case.risk_score:.2f}, executed={result['executed']})"
        )
        return result

    async def _execute_auto_approve(self, case: GovernorCase, db: Optional[AsyncSession] = None) -> bool:
        """Düşük riskli onay bekleyen projeyi QUEUED'e çeker."""
        from libs.db.repositories.repository import ProjectRepository

        async def _run(session: AsyncSession) -> bool:
            try:
                await ProjectRepository.update_fields(
                    session, uuid.UUID(case.project_id),
                    status=ProjectStatus.QUEUED,
                    notes=f"[SOFT_CEO AUTO_APPROVE] {case.rationale}",
                )
                # Bekleyen approval'ları da güncelle
                from sqlalchemy import update
                await session.execute(
                    update(ApprovalRequest)
                    .where(and_(
                        ApprovalRequest.project_id == uuid.UUID(case.project_id),
                        ApprovalRequest.status == "pending"
                    ))
                    .values(status="approved", approver_id="soft_ceo",
                            decision_at=datetime.now(timezone.utc),
                            comment=f"Soft CEO auto-approve (risk={case.risk_score:.3f})")
                )
                await session.commit()
                return True
            except Exception as e:
                logger.error(f"[Governor] Auto-approve failed: {e}")
                return False

        if db:
            return await _run(db)
        async with get_db_ctx() as session:
            return await _run(session)

    async def _execute_auto_replay(self, case: GovernorCase, db: Optional[AsyncSession] = None) -> bool:
        """Orta riskli hatalı projeyi yeniden kuyruğa alır."""
        from libs.db.repositories.repository import ProjectRepository

        async def _run(session: AsyncSession) -> bool:
            try:
                await ProjectRepository.update_fields(
                    session, uuid.UUID(case.project_id),
                    status=ProjectStatus.QUEUED,
                    retry_count=case.retry_count + 1,
                    notes=f"[SOFT_CEO AUTO_REPLAY] {case.rationale}",
                )
                await session.commit()
                # Re-enqueue
                from services.orchestration.application.job_queue import job_queue
                await job_queue.enqueue(
                    "run_project",
                    project_id=case.project_id,
                    title=case.title,
                    description="",
                    workflow_template="default",
                    quality_profile="standard",
                )
                return True
            except Exception as e:
                logger.error(f"[Governor] Auto-replay failed: {e}")
                return False

        if db:
            return await _run(db)
        async with get_db_ctx() as session:
            return await _run(session)

    async def _execute_archive(self, case: GovernorCase, db: Optional[AsyncSession] = None) -> bool:
        """Bayat ve başarısız projeyi CANCELLED'e çeker."""
        from libs.db.repositories.repository import ProjectRepository

        async def _run(session: AsyncSession) -> bool:
            try:
                await ProjectRepository.update_fields(
                    session, uuid.UUID(case.project_id),
                    status=ProjectStatus.CANCELLED,
                    cancelled_at=datetime.now(timezone.utc),
                    cancelled_by="soft_ceo",
                    notes=f"[SOFT_CEO ARCHIVE_STALE] {case.rationale}",
                )
                await session.commit()
                return True
            except Exception as e:
                logger.error(f"[Governor] Archive failed: {e}")
                return False

        if db:
            return await _run(db)
        async with get_db_ctx() as session:
            return await _run(session)

    # ── 6. Lineage Kaydı ──────────────────────────────────────
    async def emit_lineage(self, case: GovernorCase, db: Optional[AsyncSession] = None) -> None:
        """Her karar için soyağacı kaydı düşer."""
        try:
            await LineageService.log_soft_ceo_decision(
                recommended_action=case.recommended_action,
                risk_class=case.risk_class,
                pending_reason=case.pending_reason,
                target_type="project",
                target_id=case.project_id,
                rationale=case.rationale,
                confidence_score=max(0.0, 1.0 - case.risk_score),
                staleness_hours=case.staleness_hours,
                extra_meta={
                    "total_steps": case.total_steps,
                    "failed_steps": case.failed_steps,
                    "retry_count": case.retry_count,
                    "open_incidents": len(case.open_incidents),
                    "active_fingerprints": len(case.active_fingerprints),
                    "requires_operator": case.requires_operator,
                },
                db=db,
            )
        except Exception as e:
            logger.error(f"[Governor] Lineage emit failed for {case.project_id}: {e}")

    # ── Yardımcılar ───────────────────────────────────────────
    @staticmethod
    def _classify_pending_reason(
        status: str,
        approvals: List[Dict],
        incidents: List[Dict],
    ) -> str:
        """Proje durumuna göre bekleme nedenini sınıflandırır."""
        s = status.upper()
        if s in ("PENDING_APPROVAL", "WAITING_APPROVAL", "PENDING_APPROVAL_AUTO"):
            return PendingReason.PENDING_APPROVAL.value
        if s == "PAUSED":
            return PendingReason.PAUSED_WORKFLOW.value
        if s in ("ERROR", "FAILED"):
            if incidents:
                return PendingReason.OPEN_INCIDENT.value
            return PendingReason.MISSING_CONTEXT.value
        if s == "INTERRUPTED":
            return PendingReason.SAFETY_LOCK.value
        return PendingReason.STALE_QUEUE_ITEM.value

    # ── Toplu Çalıştırma ──────────────────────────────────────
    async def run_sweep(self) -> Dict[str, Any]:
        """
        Tam tarama döngüsü: tara → skorla → karar ver → uygula.
        Periyodik çağrı için tasarlandı.
        """
        summary = {
            "scanned": 0,
            "actions": {},
            "executed": 0,
            "errors": 0,
        }
        try:
            cases = await self.scan_pending_items()
            summary["scanned"] = len(cases)

            for case in cases:
                action = case.recommended_action
                summary["actions"][action] = summary["actions"].get(action, 0) + 1
                try:
                    result = await self.execute(case)
                    if result.get("executed"):
                        summary["executed"] += 1
                except Exception as e:
                    summary["errors"] += 1
                    logger.error(f"[Governor] Execute failed for {case.project_id}: {e}")

        except Exception as e:
            logger.error(f"[Governor] Sweep failed: {e}")
            summary["errors"] += 1

        logger.info(f"[Governor] Sweep complete: {summary}")
        return summary


# Singleton
approval_governor = ApprovalGovernor()
