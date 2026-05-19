"""
Soft CEO — Governor API Router (Faz 3)
Operatör inbox'u, case sorgulaması, scan tetikleme, override.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel

# from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.session import AsyncSessionLocal

from libs.db.models.governance_models import (
    GovernorAlertStatus,
)
from services.auth.jwt_auth import require_permission
from services.observability.logging import get_logger

logger = get_logger("governor_router")

router = APIRouter(tags=["Governor Inbox"])


# ── Response Schemas ──────────────────────────────────────────

class GovernorCaseOut(BaseModel):
    id: str
    project_id: str
    project_title: str
    project_status: str
    pending_reason: str
    risk_class: str
    risk_score: int
    recommended_decision: str
    decision_reason_codes: list[str] = []
    has_open_incident: bool = False
    has_safety_lock: bool = False
    has_active_fingerprint: bool = False
    requires_prime: bool = False
    requires_quorum: bool = False
    missing_context: bool = False
    stale_seconds: int = 0
    snapshot_payload: dict[str, Any] = {}
    created_at: datetime | None = None
    updated_at: datetime | None = None


class GovernorStatusOut(BaseModel):
    total_cases: int
    open_escalations: int
    auto_actions_today: int
    prime_queue: int
    quorum_queue: int
    stale_items: int
    pending_calibrations: int


class GovernorActionOut(BaseModel):
    id: str
    case_id: str | None = None
    project_id: str
    action_type: str
    status: str
    executed_by: str
    result_payload: dict[str, Any] = {}
    created_at: datetime | None = None


class GovernorEscalationOut(BaseModel):
    id: str
    case_id: str | None
    project_id: str
    escalation_type: str
    target_role: str
    reason: str
    status: str
    created_at: datetime
    resolved_at: datetime | None

class GovernorOutcomeOut(BaseModel):
    id: str
    case_id: str | None
    project_id: str
    action_id: str | None
    decision: str
    final_outcome: str
    quality: str
    was_successful: int
    operator_overrode: int
    operator_agreed: int
    resolution_latency_seconds: int
    reason_codes: list[str]
    created_at: datetime

class GovernorScorecardOut(BaseModel):
    total_decisions: int
    correct_decisions: int
    accuracy: float
    replay_success_rate: float
    avg_latency_seconds: float


class GovernorCalibrationOut(BaseModel):
    id: str
    parameter_name: str
    old_value: float
    proposed_value: float
    applied_value: float | None = None
    change_reason: str | None = None
    confidence_score: float
    window_days: int
    sample_size: int
    status: str
    approved_by: str | None = None
    created_at: datetime
    applied_at: datetime | None = None


class CalibrationActionIn(BaseModel):
    reason: str = ""


class GovernorOverrideIn(BaseModel):
    action: str  # approve, replay, no_action, escalate_quorum, archive
    reason: str = ""


class EscalationResolveIn(BaseModel):
    resolution_type: str
    resolution_notes: str
    final_action: str


class MetaGovernorDecisionOut(BaseModel):
    id: str
    project_id: str
    winning_domain: str | None
    final_decision: str
    final_risk_class: str
    reason_codes: list[str]
    applied_constraints: list[str]
    created_at: datetime


class GovernorConflictOut(BaseModel):
    id: str
    project_id: str
    domain_a: str
    domain_b: str
    decision_a: str
    decision_b: str
    conflict_type: str
    conflict_summary: str | None
    status: str
    created_at: datetime
    resolved_at: datetime | None


class GovernorRuntimeOut(BaseModel):
    domain: str
    runtime_status: str
    reason: str | None
    failure_count: int
    advisory_only: bool
    updated_at: datetime

class GovernorAlertOut(BaseModel):
    id: str
    alert_type: str
    severity: str
    status: str
    domain: str | None = None
    title: str
    summary: str
    metric_value: float | None = None
    threshold_value: float | None = None
    opened_at: datetime
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None

class GovernorMetricOut(BaseModel):
    id: str
    metric_key: str
    domain: str | None = None
    value: float
    baseline_value: float | None = None
    delta_value: float | None = None
    created_at: datetime

class GovernorDriftOut(BaseModel):
    id: str
    drift_type: str
    domain: str | None = None
    drift_score: float
    summary: str
    created_at: datetime


class GovernorDrillOut(BaseModel):
    id: str
    drill_type: str
    target_domain: str | None
    status: str
    scenario_payload: dict[str, Any]
    result_payload: dict[str, Any]
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None


class GovernorDrillIn(BaseModel):
    drill_type: str
    target_domain: str | None = None


class GovernorPolicyEvolutionOut(BaseModel):
    id: str
    policy_key: str
    evolution_type: str
    old_value: Any
    proposed_value: Any
    applied_value: Any | None = None
    change_reason: str | None = None
    confidence_score: float
    status: str
    proposed_by: str
    approved_by: str | None = None
    created_at: datetime
    applied_at: datetime | None = None


class GovernorPolicySimulationOut(BaseModel):
    id: str
    evolution_id: str
    simulation_window_days: int
    sample_size: int
    predicted_accuracy_delta: float
    predicted_false_positive_delta: float
    predicted_escalation_delta: float
    created_at: datetime


# ── Helpers ───────────────────────────────────────────────────

def _case_to_out(r) -> GovernorCaseOut:
    return GovernorCaseOut(
        id=str(r.id),
        project_id=str(r.project_id),
        project_title=r.project_title or "",
        project_status=r.project_status or "",
        pending_reason=r.pending_reason,
        risk_class=r.risk_class,
        risk_score=r.risk_score or 0,
        recommended_decision=r.recommended_decision,
        decision_reason_codes=r.decision_reason_codes or [],
        has_open_incident=bool(r.has_open_incident),
        has_safety_lock=bool(r.has_safety_lock),
        has_active_fingerprint=bool(r.has_active_fingerprint),
        requires_prime=bool(r.requires_prime),
        requires_quorum=bool(r.requires_quorum),
        missing_context=bool(r.missing_context),
        stale_seconds=r.stale_seconds or 0,
        snapshot_payload=r.snapshot_payload or {},
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


# ── Endpoints ─────────────────────────────────────────────────

@router.get("/status", response_model=GovernorStatusOut)
async def governor_status(
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    """Governor sisteminin genel durumu."""
    from sqlalchemy import func, select

    from libs.db.models.governance_models import GovernorActionRecord, GovernorCaseRecord
    from libs.db.repositories.governor_repository import (
        GovernorEscalationRepo,
    )

    async with AsyncSessionLocal() as db:
        total = (await db.execute(
            select(func.count(GovernorCaseRecord.id))
        )).scalar() or 0

        open_esc = await GovernorEscalationRepo.count_open(db)

        # Today's auto actions
        today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        auto_today = (await db.execute(
            select(func.count(GovernorActionRecord.id)).where(
                GovernorActionRecord.created_at >= today_start,
                GovernorActionRecord.status == "executed",
            )
        )).scalar() or 0

        prime_q = (await db.execute(
            select(func.count(GovernorCaseRecord.id)).where(GovernorCaseRecord.requires_prime == 1)
        )).scalar() or 0

        quorum_q = (await db.execute(
            select(func.count(GovernorCaseRecord.id)).where(GovernorCaseRecord.requires_quorum == 1)
        )).scalar() or 0

        stale = (await db.execute(
            select(func.count(GovernorCaseRecord.id)).where(GovernorCaseRecord.stale_seconds > 86400)
        )).scalar() or 0

        from libs.db.models.governance_models import CalibrationStatus, GovernorCalibrationRecord
        pending_cal = (await db.execute(
            select(func.count(GovernorCalibrationRecord.id)).where(GovernorCalibrationRecord.status == CalibrationStatus.PROPOSED)
        )).scalar() or 0

    return GovernorStatusOut(
        total_cases=total,
        open_escalations=open_esc,
        auto_actions_today=auto_today,
        prime_queue=prime_q,
        quorum_queue=quorum_q,
        stale_items=stale,
        pending_calibrations=pending_cal
    )


@router.get("/cases", response_model=list[GovernorCaseOut])
async def list_governor_cases(
    response: Response,
    risk_class: str | None = None,
    recommended_decision: str | None = None,
    pending_reason: str | None = None,
    project_status: str | None = None,
    _start: int = Query(0, alias="_start"),
    _end: int = Query(50, alias="_end"),
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    """Filtrelenmiş governor case listesi."""
    from libs.db.repositories.governor_repository import GovernorCaseRepo

    limit = _end - _start
    async with AsyncSessionLocal() as db:
        items, total = await GovernorCaseRepo.list_cases(
            db, limit=limit, offset=_start,
            risk_class=risk_class,
            recommended_decision=recommended_decision,
            pending_reason=pending_reason,
            project_status=project_status,
        )

    response.headers["x-total-count"] = str(total)
    response.headers["Access-Control-Expose-Headers"] = "x-total-count"
    return [_case_to_out(r) for r in items]


@router.get("/cases/{case_id}", response_model=GovernorCaseOut)
async def get_governor_case(
    case_id: str,
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    """Tek bir governor case detayı."""
    from libs.db.repositories.governor_repository import GovernorCaseRepo

    async with AsyncSessionLocal() as db:
        record = await GovernorCaseRepo.get_case(db, case_id)
    if not record:
        raise HTTPException(status_code=404, detail="Case not found")
    return _case_to_out(record)


@router.post("/scan")
async def trigger_governor_scan(
    identity: dict[str, Any] = Depends(require_permission("governor.scan")),
):
    """Elle tetiklenen governor taraması."""
    from services.governance.approval_governor import approval_governor
    summary = await approval_governor.run_sweep()
    return {"status": "completed", "summary": summary}


@router.post("/cases/{case_id}/execute")
async def execute_governor_case(
    case_id: str,
    identity: dict[str, Any] = Depends(require_permission("governor.execute")),
):
    """LOW/MEDIUM risk case'lerini uygular."""
    from libs.db.repositories.governor_repository import GovernorCaseRepo
    from services.governance.approval_governor import GovernorCase, approval_governor

    async with AsyncSessionLocal() as db:
        record = await GovernorCaseRepo.get_case(db, case_id)
    if not record:
        raise HTTPException(status_code=404, detail="Case not found")

    # HIGH/CRITICAL riskli case'ler execute edilemez
    if record.risk_class in ("HIGH", "CRITICAL"):
        raise HTTPException(
            status_code=403,
            detail=f"Risk class {record.risk_class} requires manual PRIME/Quorum review."
        )

    # Minimal case reconstruct for execution
    case = GovernorCase(
        project_id=str(record.project_id),
        title=record.project_title or "",
        status=record.project_status or "",
        source="CONTROL_PLANE",
        priority=record.snapshot_payload.get("priority", "MEDIUM") if record.snapshot_payload else "MEDIUM",
        recommended_action=record.recommended_decision,
        risk_score=record.risk_score / 1000.0,
        risk_class=record.risk_class,
        pending_reason=record.pending_reason,
        rationale="; ".join([str(c) for c in (record.decision_reason_codes or [])]),
    )
    result = await approval_governor.execute(case)
    return {"status": "ok", "result": result}


@router.post("/cases/{case_id}/override")
async def override_governor_case(
    case_id: str,
    body: GovernorOverrideIn,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    """Operatör manuel karar girer."""
    from libs.db.repositories.governor_repository import GovernorActionRepo, GovernorCaseRepo
    from services.governance.approval_governor_execution_policy import execution_policy
    from services.governance.lineage_service import LineageService

    if len((body.reason or "").strip()) < 20:
        raise HTTPException(status_code=400, detail="INVALID_JUSTIFICATION: Override işlemi için en az 20 karakterlik gerekçe zorunludur.")

    operator_role = identity.get("role", "HUMAN_OPERATOR")
    operator_name = identity.get("name", "unknown")

    async with AsyncSessionLocal() as db:
        record = await GovernorCaseRepo.get_case(db, case_id)
        if not record:
            raise HTTPException(status_code=404, detail="Case not found")

        allowed, msg = execution_policy.can_override(record, operator_role, body.action, body.reason)
        if not allowed:
            raise HTTPException(status_code=403, detail=msg)

        # Action kaydı
        await GovernorActionRepo.save_action(
            db,
            case_id=case_id,
            project_id=str(record.project_id),
            action_type=f"OVERRIDE_{body.action.upper()}",
            status="executed",
            executed_by=f"OPERATOR:{operator_name}",
            result_payload={"reason": body.reason, "original_decision": record.recommended_decision},
            justification=body.reason,
            operator_role=operator_role,
            override_flag=1,
            guardrail_bypassed=1 if record.risk_class in ("HIGH", "CRITICAL") else 0,
            approval_snapshot={"risk": record.risk_score, "operator": operator_name}
        )

        # Case'i güncelle
        record.recommended_decision = f"OVERRIDE_{body.action.upper()}"
        record.decision_reason_codes = [body.reason]

        await db.commit()

        # Outcome kaydet (Override olduğu için hemen kaydediyoruz)
        # from services.governance.approval_governor import ApprovalGovernor
        # governor = ApprovalGovernor()
        # await governor._record_outcome_for_case(case_id, str(record.project_id), override_action=body.action, db=db)
        logger.info(f"Outcome recorded via override for case {case_id}")

    # Lineage kaydı
    await LineageService.log_soft_ceo_decision(
        recommended_action=f"OVERRIDE_{body.action.upper()}",
        risk_class=record.risk_class,
        pending_reason=record.pending_reason,
        target_type="project",
        target_id=str(record.project_id),
        rationale=f"Operator override by {identity.get('name')}: {body.reason}",
        confidence_score=1.0,
        staleness_hours=record.stale_seconds / 3600.0,
        extra_meta={"override_by": identity.get("name"), "original_decision": record.recommended_decision},
    )

    return {"status": "overridden", "action": body.action, "case_id": case_id}

@router.post("/cases/{case_id}/restore")
async def restore_governor_case(
    case_id: str,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    """Arşivlenmiş bir case'i geri alır."""
    from sqlalchemy import select

    from libs.db.repositories.governor_repository import GovernorActionRepo, GovernorCaseRepo
    from libs.db.repositories.repository import ProjectRepository
    from services.governance.approval_governor_execution_policy import execution_policy

    operator_role = identity.get("role", "HUMAN_OPERATOR")

    async with AsyncSessionLocal() as db:
        record = await GovernorCaseRepo.get_case(db, case_id)
        if not record:
            raise HTTPException(status_code=404, detail="Case not found")

        # Find the archive action
        from libs.db.models.governance_models import GovernorActionRecord
        action_res = await db.execute(
            select(GovernorActionRecord)
            .where(GovernorActionRecord.case_id == uuid.UUID(case_id))
            .where(GovernorActionRecord.action_type == "ARCHIVE_STALE")
            .order_by(GovernorActionRecord.created_at.desc())
        )
        action = action_res.scalars().first()

        if not action or "previous_status" not in action.result_payload:
            raise HTTPException(status_code=400, detail="Bu case arşivlenmemiş veya geri alma verisi yok.")

        archived_at_str = action.result_payload.get("archived_at")
        if not archived_at_str:
            raise HTTPException(status_code=400, detail="Arşiv tarihi bulunamadı.")

        archived_at = datetime.fromisoformat(archived_at_str)

        case_mock = type('obj', (object,), {
            'has_safety_lock': record.has_safety_lock
        })
        allowed, msg = execution_policy.can_restore(case_mock, operator_role, archived_at)
        if not allowed:
            raise HTTPException(status_code=403, detail=msg)

        prev_status = action.result_payload["previous_status"]
        await ProjectRepository.update_fields(db, record.project_id, status=prev_status)

        await GovernorActionRepo.save_action(
            db,
            case_id=case_id,
            project_id=str(record.project_id),
            action_type="RESTORE_ARCHIVE",
            status="executed",
            executed_by=f"OPERATOR:{identity.get('name', 'unknown')}",
            result_payload={"restored_from": "ARCHIVE_STALE", "new_status": prev_status},
        )
        await db.commit()

    return {"status": "restored", "new_project_status": prev_status}


@router.get("/escalations", response_model=list[GovernorEscalationOut])
async def list_escalations(
    response: Response,
    _start: int = Query(0, alias="_start"),
    _end: int = Query(50, alias="_end"),
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    """Açık ve değerlendirme aşamasındaki eskalasyonları listeler."""
    from libs.db.repositories.governor_repository import GovernorEscalationRepo

    async with AsyncSessionLocal() as db:
        items = await GovernorEscalationRepo.list_active(db, limit=_end - _start)

    response.headers["x-total-count"] = str(len(items))
    response.headers["Access-Control-Expose-Headers"] = "x-total-count"
    return [
        GovernorEscalationOut(
            id=str(e.id),
            case_id=str(e.case_id) if e.case_id else None,
            project_id=str(e.project_id),
            escalation_type=e.escalation_type,
            target_role=e.target_role,
            reason=e.reason or "",
            status=e.status,
            created_at=e.created_at,
            resolved_at=e.resolved_at,
        ) for e in items
    ]


@router.post("/escalations/{escalation_id}/ack")
async def ack_escalation(
    escalation_id: str,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    from libs.db.repositories.governor_repository import GovernorEscalationRepo
    async with AsyncSessionLocal() as db:
        await GovernorEscalationRepo.update_status(db, escalation_id, status="acknowledged")
        await db.commit()
    return {"status": "acknowledged"}


@router.post("/escalations/{escalation_id}/resolve")
async def resolve_escalation(
    escalation_id: str,
    body: EscalationResolveIn,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    from libs.db.repositories.governor_repository import GovernorEscalationRepo
    async with AsyncSessionLocal() as db:
        await GovernorEscalationRepo.update_status(
            db, escalation_id, status="resolved",
            resolution_type=body.resolution_type,
            resolution_notes=body.resolution_notes,
            resolved_by=identity.get("name", "unknown"),
            final_action=body.final_action
        )

        # Outcome kaydet
        from sqlalchemy import select

        from libs.db.models.governance_models import GovernorEscalationRecord
        from services.governance.approval_governor import ApprovalGovernor

        governor = ApprovalGovernor()
        # Find the case_id first
        esc = await db.execute(select(GovernorEscalationRecord).where(GovernorEscalationRecord.id == uuid.UUID(escalation_id)))
        esc_record = esc.scalar_one_or_none()
        if esc_record and esc_record.case_id:
            await governor._record_outcome_for_case(str(esc_record.case_id), str(esc_record.project_id), override_action=body.final_action, db=db)

        await db.commit()
    return {"status": "resolved"}


@router.post("/escalations/{escalation_id}/cancel")
async def cancel_escalation(
    escalation_id: str,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    from libs.db.repositories.governor_repository import GovernorEscalationRepo
    async with AsyncSessionLocal() as db:
        await GovernorEscalationRepo.update_status(
            db, escalation_id, status="cancelled",
            resolved_by=identity.get("name", "unknown")
        )
        await db.commit()
    return {"status": "cancelled"}


@router.get("/outcomes", response_model=list[GovernorOutcomeOut])
async def list_outcomes(
    response: Response,
    _start: int = Query(0, alias="_start"),
    _end: int = Query(50, alias="_end"),
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    from sqlalchemy import func, select

    from libs.db.models.governance_models import GovernorOutcomeRecord
    from libs.db.repositories.governor_outcome_repository import GovernorOutcomeRepo

    async with AsyncSessionLocal() as db:
        items = await GovernorOutcomeRepo.list_recent(db, limit=_end - _start, offset=_start)
        # Total count needs another query or count
        total = (await db.execute(select(func.count(GovernorOutcomeRecord.id)))).scalar() or 0

    response.headers["x-total-count"] = str(total)
    response.headers["Access-Control-Expose-Headers"] = "x-total-count"

    return [
        GovernorOutcomeOut(
            id=str(o.id),
            case_id=str(o.case_id) if o.case_id else None,
            project_id=str(o.project_id),
            action_id=str(o.action_id) if o.action_id else None,
            decision=o.decision,
            final_outcome=o.final_outcome.value,
            quality=o.quality.value,
            was_successful=o.was_successful,
            operator_overrode=o.operator_overrode,
            operator_agreed=o.operator_agreed,
            resolution_latency_seconds=o.resolution_latency_seconds,
            reason_codes=o.reason_codes or [],
            created_at=o.created_at
        ) for o in items
    ]


@router.get("/calibrations", response_model=list[GovernorCalibrationOut])
async def list_calibrations(
    limit: int = Query(50),
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    from libs.db.repositories.governor_calibration_repository import GovernorCalibrationRepo
    async with AsyncSessionLocal() as db:
        items = await GovernorCalibrationRepo.list_recent(db, limit=limit)

    return [
        GovernorCalibrationOut(
            id=str(c.id),
            parameter_name=c.parameter_name,
            old_value=c.old_value,
            proposed_value=c.proposed_value,
            applied_value=c.applied_value,
            change_reason=c.change_reason,
            confidence_score=c.confidence_score,
            window_days=c.window_days,
            sample_size=c.sample_size,
            status=c.status.value,
            approved_by=c.approved_by,
            created_at=c.created_at,
            applied_at=c.applied_at
        ) for c in items
    ]


@router.post("/calibrations/propose")
async def propose_calibrations(
    window_days: int = Query(14),
    identity: dict[str, Any] = Depends(require_permission("governor.scan")),
):
    """Calibriton engine'i tetikler ve yeni öneriler oluşturur."""
    from services.governance.approval_governor_calibration import ApprovalGovernorCalibration
    async with AsyncSessionLocal() as db:
        engine = ApprovalGovernorCalibration(db)
        proposals = await engine.generate_calibration_proposals(window_days=window_days)
        await db.commit()

    return {"status": "ok", "proposals_count": len(proposals), "ids": [str(p) for p in proposals]}


@router.post("/calibrations/{cal_id}/approve")
async def approve_calibration(
    cal_id: str,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    from libs.db.repositories.governor_calibration_repository import GovernorCalibrationRepo
    operator_name = identity.get("name", "unknown")

    async with AsyncSessionLocal() as db:
        success = await GovernorCalibrationRepo.apply_calibration(db, uuid.UUID(cal_id), operator_name)
        if not success:
            raise HTTPException(status_code=400, detail="Calibration not found or not in PROPOSED status.")
        await db.commit()

    return {"status": "applied"}


@router.post("/calibrations/{cal_id}/reject")
async def reject_calibration(
    cal_id: str,
    body: CalibrationActionIn,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    from libs.db.repositories.governor_calibration_repository import GovernorCalibrationRepo
    operator_name = identity.get("name", "unknown")

    async with AsyncSessionLocal() as db:
        success = await GovernorCalibrationRepo.reject_calibration(db, uuid.UUID(cal_id), operator_name, body.reason)
        if not success:
            raise HTTPException(status_code=400, detail="Calibration not found or not in PROPOSED status.")
        await db.commit()

    return {"status": "rejected"}


@router.post("/calibrations/{cal_id}/rollback")
async def rollback_calibration(
    cal_id: str,
    body: CalibrationActionIn,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    from libs.db.repositories.governor_calibration_repository import GovernorCalibrationRepo
    operator_name = identity.get("name", "unknown")

    async with AsyncSessionLocal() as db:
        success = await GovernorCalibrationRepo.rollback_calibration(db, uuid.UUID(cal_id), operator_name, body.reason)
        if not success:
            raise HTTPException(status_code=400, detail="Calibration not found or not in APPLIED status.")
        await db.commit()

    return {"status": "rolled_back"}


@router.get("/scorecard", response_model=GovernorScorecardOut)
async def get_scorecard(
    window_days: int = Query(7),
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    from libs.db.repositories.governor_outcome_repository import GovernorOutcomeRepo
    async with AsyncSessionLocal() as db:
        metrics = await GovernorOutcomeRepo.aggregate_metrics(db, window_days=window_days)

    return GovernorScorecardOut(**metrics)


# ── Meta Governor Endpoints ────────────────────────────────────

@router.post("/meta/scan/{project_id}")
async def meta_scan_project(
    project_id: str,
    identity: dict[str, Any] = Depends(require_permission("governor.scan")),
):
    """Federated Governor taramasını tek bir proje için tetikler."""
    from services.governance.meta_governor import MetaGovernor
    meta = MetaGovernor()
    result = await meta.scan_project(uuid.UUID(project_id))
    return result


@router.get("/meta/decisions", response_model=list[MetaGovernorDecisionOut])
async def list_meta_decisions(
    project_id: str | None = None,
    limit: int = Query(20),
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    """Federated meta kararları listeler."""
    from libs.db.repositories.meta_governor_repository import MetaGovernorRepo
    async with AsyncSessionLocal() as db:
        items = await MetaGovernorRepo.list_meta_decisions(
            db, project_id=uuid.UUID(project_id) if project_id else None, limit=limit
        )

    return [
        MetaGovernorDecisionOut(
            id=str(r.id),
            project_id=str(r.project_id),
            winning_domain=r.winning_domain.value if r.winning_domain else None,
            final_decision=r.final_decision,
            final_risk_class=r.final_risk_class,
            reason_codes=r.reason_codes or [],
            applied_constraints=r.applied_constraints or [],
            created_at=r.created_at
        ) for r in items
    ]


@router.get("/meta/conflicts", response_model=list[GovernorConflictOut])
async def list_governor_conflicts(
    project_id: str | None = None,
    status: str = Query("open"),
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    """Domain governor'lar arasındaki çakışmaları listeler."""
    from libs.db.repositories.meta_governor_repository import GovernorConflictRepo
    async with AsyncSessionLocal() as db:
        items = await GovernorConflictRepo.list_conflicts(
            db, project_id=uuid.UUID(project_id) if project_id else None, status=status
        )

    return [
        GovernorConflictOut(
            id=str(r.id),
            project_id=str(r.project_id),
            domain_a=r.domain_a.value,
            domain_b=r.domain_b.value,
            decision_a=r.decision_a,
            decision_b=r.decision_b,
            conflict_type=r.conflict_type.value,
            conflict_summary=r.conflict_summary,
            status=r.status,
            created_at=r.created_at,
            resolved_at=r.resolved_at
        ) for r in items
    ]


@router.post("/meta/conflicts/{conflict_id}/resolve")
async def resolve_governor_conflict(
    conflict_id: str,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    """Bir çakışmayı manuel olarak çözüldü işaretler."""
    from libs.db.repositories.meta_governor_repository import GovernorConflictRepo
    async with AsyncSessionLocal() as db:
        success = await GovernorConflictRepo.resolve_conflict(db, uuid.UUID(conflict_id))
        if not success:
            raise HTTPException(status_code=404, detail="Conflict not found")
        await db.commit()
    return {"status": "resolved"}


# ── Resilience & Chaos Endpoints ──────────────────────────────

@router.get("/resilience/status", response_model=list[GovernorRuntimeOut])
async def get_resilience_status(
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    """Tüm domain'lerin çalışma (resilience) durumunu listeler."""
    from services.governance.governor_resilience_manager import GovernorResilienceManager
    async with AsyncSessionLocal() as db:
        status_list = await GovernorResilienceManager.get_all_runtime_status(db)
        # We need to fetch real records for updated_at or refine the manager method
        from libs.db.models.governance_models import GovernorDomain
        from libs.db.repositories.governor_resilience_repository import GovernorResilienceRepo

        results = []
        for s in status_list:
            record = await GovernorResilienceRepo.get_runtime_status(db, GovernorDomain(s["domain"]))
            if record:
                results.append(GovernorRuntimeOut(
                    domain=s["domain"],
                    runtime_status=s["status"],
                    reason=record.reason,
                    failure_count=s["failure_count"],
                    advisory_only=s["advisory_only"],
                    updated_at=record.updated_at
                ))
        return results


@router.post("/resilience/drills", response_model=dict[str, Any])
async def start_chaos_drill(
    body: GovernorDrillIn,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    """Yeni bir kaos tatbikatı (drill) başlatır."""
    from libs.db.models.governance_models import (
        GovernorDomain,
        GovernorDrillType,
    )
    from services.governance.governor_chaos_lab import GovernorChaosLab

    async with AsyncSessionLocal() as db:
        drill_type = GovernorDrillType(body.drill_type)
        target = GovernorDomain(body.target_domain) if body.target_domain else None

        result = await GovernorChaosLab.run_drill(
            db, drill_type, target, created_by=identity.get("name", "unknown")
        )
        await db.commit()
        return result


@router.get("/resilience/drills", response_model=list[GovernorDrillOut])
async def list_chaos_drills(
    limit: int = Query(20),
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    """Geçmiş ve aktif tatbikatları listeler."""
    from sqlalchemy import desc, select

    from libs.db.models.governance_models import GovernorDrillRecord
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(GovernorDrillRecord).order_by(desc(GovernorDrillRecord.created_at)).limit(limit))
        items = res.scalars().all()

    return [
        GovernorDrillOut(
            id=str(r.id),
            drill_type=r.drill_type.value,
            target_domain=r.target_domain.value if r.target_domain else None,
            status=r.status.value,
            scenario_payload=r.scenario_payload or {},
            result_payload=r.result_payload or {},
            created_at=r.created_at,
            started_at=r.started_at,
            completed_at=r.completed_at
        ) for r in items
    ]

# ── Proof Fabric Endpoints (Phase 11) ───────────────────────

class ProofEventOut(BaseModel):
    id: str
    event_type: str
    domain: str | None
    entity_id: str | None
    event_hash: str
    chain_index: int
    created_at: datetime

class ProofSnapshotOut(BaseModel):
    id: str
    snapshot_name: str
    merkle_root: str
    snapshot_hash: str
    event_count: int
    seal_status: str
    created_at: datetime

@router.get("/proof/events", response_model=list[ProofEventOut])
async def list_proof_events(
    limit: int = Query(50),
    identity: dict[str, Any] = Depends(require_permission("governance.proof.view")),
):
    from sqlalchemy import desc, select

    from libs.db.models.governance_models import GovernanceProofEventRecord
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(GovernanceProofEventRecord).order_by(desc(GovernanceProofEventRecord.chain_index)).limit(limit))
        items = res.scalars().all()
    return [
        ProofEventOut(
            id=str(r.id),
            event_type=r.event_type.value,
            domain=r.domain.value if r.domain else None,
            entity_id=r.entity_id,
            event_hash=r.event_hash,
            chain_index=r.chain_index,
            created_at=r.created_at
        ) for r in items
    ]

@router.get("/proof/snapshots", response_model=list[ProofSnapshotOut])
async def list_proof_snapshots(
    identity: dict[str, Any] = Depends(require_permission("governance.proof.view")),
):
    import hashlib

    from sqlalchemy import desc, select

    from libs.db.models.governance_models import (
        GovernanceProofEventRecord,
        GovernanceProofSnapshotRecord,
        ProofSealStatus,
    )
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(GovernanceProofSnapshotRecord).order_by(desc(GovernanceProofSnapshotRecord.created_at)))
        items = res.scalars().all()
        if not items:
            event_res = await db.execute(
                select(GovernanceProofEventRecord).order_by(GovernanceProofEventRecord.chain_index.asc())
            )
            proof_events = event_res.scalars().all()
            if proof_events:
                combined_hashes = "".join(event.event_hash for event in proof_events)
                merkle_root = hashlib.sha256(combined_hashes.encode("utf-8")).hexdigest()
                snapshot_hash = hashlib.sha256(
                    f"derived-proof|{merkle_root}|{len(proof_events)}".encode()
                ).hexdigest()
                return [
                    ProofSnapshotOut(
                        id="derived-local-proof-snapshot",
                        snapshot_name="LOCAL_DERIVED_PROOF_SNAPSHOT",
                        merkle_root=merkle_root,
                        snapshot_hash=snapshot_hash,
                        event_count=len(proof_events),
                        seal_status=ProofSealStatus.SEALED.value,
                        created_at=proof_events[-1].created_at,
                    )
                ]
    return [
        ProofSnapshotOut(
            id=str(r.id),
            snapshot_name=r.snapshot_name,
            merkle_root=r.merkle_root,
            snapshot_hash=r.snapshot_hash,
            event_count=r.event_count,
            seal_status=r.seal_status.value,
            created_at=r.created_at
        ) for r in items
    ]

@router.post("/proof/snapshots/seal")
async def seal_manual_snapshot(
    name: str = Query(...),
    identity: dict[str, Any] = Depends(require_permission("governance.proof.seal")),
):
    from libs.db.session import SessionLocal
    from services.governance.proof_fabric import ProofFabric
    with SessionLocal() as db:
        fabric = ProofFabric(db)
        # Find start idx

        from libs.db.models.governance_models import (
            GovernanceProofEventRecord,
            GovernanceProofSnapshotRecord,
        )
        last_snap = db.query(GovernanceProofSnapshotRecord).order_by(GovernanceProofSnapshotRecord.end_chain_index.desc()).first()
        start_idx = (last_snap.end_chain_index + 1) if last_snap else 0

        last_event = db.query(GovernanceProofEventRecord).order_by(GovernanceProofEventRecord.chain_index.desc()).first()
        if not last_event:
            raise HTTPException(status_code=400, detail="No events to seal")

        snap = fabric.seal_snapshot(name, start_idx, last_event.chain_index, actor=identity.get("name"))
        return {"status": "sealed", "snapshot_id": str(snap.id)}

@router.get("/proof/verify/snapshot/{snapshot_id}")
async def verify_snapshot_api(
    snapshot_id: str,
    identity: dict[str, Any] = Depends(require_permission("governance.proof.verify")),
):
    from libs.db.session import SessionLocal
    from services.governance.proof_verifier import ProofVerifier
    with SessionLocal() as db:
        verifier = ProofVerifier(db)
        result = verifier.verify_snapshot(uuid.UUID(snapshot_id))
        return result

@router.post("/proof/export/{snapshot_id}")
async def export_audit_bundle_api(
    snapshot_id: str,
    identity: dict[str, Any] = Depends(require_permission("governance.proof.export")),
):
    from libs.db.session import SessionLocal
    from services.governance.proof_bundle_exporter import AuditBundleExporter
    with SessionLocal() as db:
        exporter = AuditBundleExporter(db)
        path = exporter.export_bundle(snapshot_id, "exports/audit")
        return {"status": "exported", "path": path}
# ── Observability Endpoints ───────────────────────────────────

@router.get("/alerts", response_model=list[GovernorAlertOut])
async def list_governor_alerts(
    limit: int = Query(50),
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    """Açık yönetişim uyarılarını listeler."""
    from libs.db.repositories.governor_observability_repository import GovernorAlertRepo
    async with AsyncSessionLocal() as db:
        items = await GovernorAlertRepo.list_open_alerts(db, limit=limit)

    return [
        GovernorAlertOut(
            id=str(r.id),
            alert_type=r.alert_type.value,
            severity=r.severity.value,
            status=r.status.value,
            domain=r.domain.value if r.domain else None,
            title=r.title,
            summary=r.summary,
            metric_value=r.metric_value,
            threshold_value=r.threshold_value,
            opened_at=r.opened_at,
            acknowledged_at=r.acknowledged_at,
            resolved_at=r.resolved_at
        ) for r in items
    ]

@router.post("/alerts/{alert_id}/ack")
async def ack_governor_alert(
    alert_id: str,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    """Bir uyarıyı onaylar (Acknowledge)."""
    from libs.db.repositories.governor_observability_repository import GovernorAlertRepo
    async with AsyncSessionLocal() as db:
        success = await GovernorAlertRepo.update_status(
            db, uuid.UUID(alert_id), GovernorAlertStatus.ACKNOWLEDGED, owner_id=identity.get("name")
        )
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        await db.commit()
    return {"status": "acknowledged"}

@router.post("/alerts/{alert_id}/resolve")
async def resolve_governor_alert(
    alert_id: str,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    """Bir uyarıyı çözüldü olarak işaretler."""
    from libs.db.repositories.governor_observability_repository import GovernorAlertRepo
    async with AsyncSessionLocal() as db:
        success = await GovernorAlertRepo.update_status(
            db, uuid.UUID(alert_id), GovernorAlertStatus.RESOLVED
        )
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        await db.commit()
    return {"status": "resolved"}

@router.get("/metrics", response_model=list[GovernorMetricOut])
async def list_governor_metrics(
    limit: int = Query(20),
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    """Yönetişim metriklerini listeler."""
    from libs.db.repositories.governor_observability_repository import GovernorMetricAggregateRepo
    async with AsyncSessionLocal() as db:
        items = await GovernorMetricAggregateRepo.get_latest_metrics(db, limit=limit)

    return [
        GovernorMetricOut(
            id=str(r.id),
            metric_key=r.metric_key,
            domain=r.domain,
            value=r.value,
            baseline_value=r.baseline_value,
            delta_value=r.delta_value,
            created_at=r.created_at
        ) for r in items
    ]

@router.get("/drifts", response_model=list[GovernorDriftOut])
async def list_governor_drifts(
    limit: int = Query(50),
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    """Yönetişim sapmalarını (drift) listeler."""
    from libs.db.repositories.governor_observability_repository import GovernorDriftRepo
    async with AsyncSessionLocal() as db:
        items = await GovernorDriftRepo.list_recent_drifts(db, limit=limit)

    return [
        GovernorDriftOut(
            id=str(r.id),
            drift_type=r.drift_type.value,
            domain=r.domain.value if r.domain else None,
            drift_score=r.drift_score,
            summary=r.summary,
            created_at=r.created_at
        ) for r in items
    ]
