"""
Soft CEO — Governor Repository Layer (Faz 3)
Case, Action, Escalation persistence for the Approval Governor.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bilgeapi.libs.db.models.governance_models import (
    GovernorActionRecord,
    GovernorCaseRecord,
    GovernorEscalationRecord,
)
from bilgeapi.services.observability.logging import get_logger

logger = get_logger("db.governor_repo")


class GovernorCaseRepo:

    @staticmethod
    async def upsert_case(db: AsyncSession, data: dict[str, Any]) -> GovernorCaseRecord:
        """Aynı project_id için varsa güncelle, yoksa oluştur."""
        project_id = data["project_id"]
        try:
            uid = uuid.UUID(str(project_id))
        except ValueError:
            uid = project_id

        res = await db.execute(
            select(GovernorCaseRecord).where(GovernorCaseRecord.project_id == uid)
        )
        existing = res.scalar_one_or_none()

        if existing:
            for key, val in data.items():
                if key != "id" and hasattr(existing, key):
                    setattr(existing, key, val)
            existing.updated_at = datetime.now(UTC)
            await db.flush()
            return existing

        record = GovernorCaseRecord(project_id=uid, **{
            k: v for k, v in data.items() if k not in ("id", "project_id")
        })
        db.add(record)
        await db.flush()
        return record

    @staticmethod
    async def get_case(db: AsyncSession, case_id: str) -> GovernorCaseRecord | None:
        res = await db.execute(
            select(GovernorCaseRecord).where(GovernorCaseRecord.id == uuid.UUID(case_id))
        )
        return res.scalar_one_or_none()

    @staticmethod
    async def get_case_by_project(db: AsyncSession, project_id: str) -> GovernorCaseRecord | None:
        res = await db.execute(
            select(GovernorCaseRecord).where(GovernorCaseRecord.project_id == uuid.UUID(project_id))
        )
        return res.scalar_one_or_none()

    @staticmethod
    async def list_cases(
        db: AsyncSession,
        limit: int = 50,
        offset: int = 0,
        risk_class: str | None = None,
        recommended_decision: str | None = None,
        pending_reason: str | None = None,
        project_status: str | None = None,
    ) -> tuple[list[GovernorCaseRecord], int]:
        """Filtrelenmiş case listesi + toplam sayı."""
        q = select(GovernorCaseRecord)
        count_q = select(func.count(GovernorCaseRecord.id))

        filters = []
        if risk_class:
            filters.append(GovernorCaseRecord.risk_class == risk_class)
        if recommended_decision:
            filters.append(GovernorCaseRecord.recommended_decision == recommended_decision)
        if pending_reason:
            filters.append(GovernorCaseRecord.pending_reason == pending_reason)
        if project_status:
            filters.append(GovernorCaseRecord.project_status == project_status)

        if filters:
            q = q.where(and_(*filters))
            count_q = count_q.where(and_(*filters))

        total = (await db.execute(count_q)).scalar() or 0

        q = q.order_by(GovernorCaseRecord.updated_at.desc()).limit(limit).offset(offset)
        items = (await db.execute(q)).scalars().all()
        return items, total


class GovernorActionRepo:

    @staticmethod
    async def save_action(
        db: AsyncSession,
        case_id: str | None,
        project_id: str,
        action_type: str,
        status: str = "executed",
        executed_by: str = "SOFT_CEO",
        result_payload: dict | None = None,
        justification: str | None = None,
        operator_role: str | None = None,
        override_flag: int = 0,
        guardrail_bypassed: int = 0,
        approval_snapshot: dict | None = None,
    ) -> GovernorActionRecord:
        record = GovernorActionRecord(
            case_id=uuid.UUID(case_id) if case_id else None,
            project_id=uuid.UUID(project_id),
            action_type=action_type,
            status=status,
            executed_by=executed_by,
            result_payload=result_payload or {},
            justification=justification,
            operator_role=operator_role,
            override_flag=override_flag,
            guardrail_bypassed=guardrail_bypassed,
            approval_snapshot=approval_snapshot or {},
        )
        db.add(record)
        await db.flush()
        return record

    @staticmethod
    async def get_recent_replay_actions(
        db: AsyncSession,
        project_id: str,
        within_minutes: int = 30
    ) -> int:
        from datetime import datetime, timedelta
        cutoff = datetime.now(UTC) - timedelta(minutes=within_minutes)
        q = select(func.count(GovernorActionRecord.id)).where(
            and_(
                GovernorActionRecord.project_id == uuid.UUID(project_id),
                GovernorActionRecord.action_type.in_(["AUTO_REPLAY_CANDIDATE", "OVERRIDE_REPLAY"]),
                GovernorActionRecord.created_at >= cutoff
            )
        )
        return (await db.execute(q)).scalar() or 0

    @staticmethod
    async def list_actions(
        db: AsyncSession,
        project_id: str | None = None,
        limit: int = 20,
    ) -> list[GovernorActionRecord]:
        q = select(GovernorActionRecord).order_by(GovernorActionRecord.created_at.desc()).limit(limit)
        if project_id:
            q = q.where(GovernorActionRecord.project_id == uuid.UUID(project_id))
        return (await db.execute(q)).scalars().all()


class GovernorEscalationRepo:

    @staticmethod
    async def save_escalation(
        db: AsyncSession,
        case_id: str | None,
        project_id: str,
        escalation_type: str,
        target_role: str = "SOVEREIGN_PRIME",
        reason: str = "",
    ) -> GovernorEscalationRecord:
        record = GovernorEscalationRecord(
            case_id=uuid.UUID(case_id) if case_id else None,
            project_id=uuid.UUID(project_id),
            escalation_type=escalation_type,
            target_role=target_role,
            reason=reason,
        )
        db.add(record)
        await db.flush()
        return record

    @staticmethod
    async def get_escalation(db: AsyncSession, escalation_id: str) -> GovernorEscalationRecord | None:
        res = await db.execute(select(GovernorEscalationRecord).where(GovernorEscalationRecord.id == uuid.UUID(escalation_id)))
        return res.scalar_one_or_none()

    @staticmethod
    async def update_status(
        db: AsyncSession,
        escalation_id: str,
        status: str,
        resolution_type: str | None = None,
        resolution_notes: str | None = None,
        resolved_by: str | None = None,
        final_action: str | None = None
    ) -> bool:
        values = {"status": status}
        if status in ["resolved", "cancelled"]:
            values["resolved_at"] = datetime.now(UTC)
            if resolution_type: values["resolution_type"] = resolution_type
            if resolution_notes: values["resolution_notes"] = resolution_notes
            if resolved_by: values["resolved_by"] = resolved_by
            if final_action: values["final_action"] = final_action

        await db.execute(
            update(GovernorEscalationRecord)
            .where(GovernorEscalationRecord.id == uuid.UUID(escalation_id))
            .values(**values)
        )
        await db.flush()
        return True

    @staticmethod
    async def list_active(db: AsyncSession, limit: int = 50) -> list[GovernorEscalationRecord]:
        q = (
            select(GovernorEscalationRecord)
            .where(GovernorEscalationRecord.status.in_(["open", "acknowledged", "in_review"]))
            .order_by(GovernorEscalationRecord.created_at.asc())
            .limit(limit)
        )
        return (await db.execute(q)).scalars().all()

    @staticmethod
    async def count_open(db: AsyncSession) -> int:
        return (await db.execute(
            select(func.count(GovernorEscalationRecord.id))
            .where(GovernorEscalationRecord.status == "open")
        )).scalar() or 0
