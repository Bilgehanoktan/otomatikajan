"""
Soft CEO — Governor Repository Layer (Faz 3)
Case, Action, Escalation persistence for the Approval Governor.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from libs.db.models.governance_models import (
    GovernorCaseRecord, GovernorActionRecord, GovernorEscalationRecord,
)
from libs.db.session import get_db_ctx
from services.observability.logging import get_logger

logger = get_logger("db.governor_repo")


class GovernorCaseRepo:

    @staticmethod
    async def upsert_case(db: AsyncSession, data: Dict[str, Any]) -> GovernorCaseRecord:
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
            existing.updated_at = datetime.now(timezone.utc)
            await db.flush()
            return existing

        record = GovernorCaseRecord(project_id=uid, **{
            k: v for k, v in data.items() if k not in ("id", "project_id")
        })
        db.add(record)
        await db.flush()
        return record

    @staticmethod
    async def get_case(db: AsyncSession, case_id: str) -> Optional[GovernorCaseRecord]:
        res = await db.execute(
            select(GovernorCaseRecord).where(GovernorCaseRecord.id == uuid.UUID(case_id))
        )
        return res.scalar_one_or_none()

    @staticmethod
    async def get_case_by_project(db: AsyncSession, project_id: str) -> Optional[GovernorCaseRecord]:
        res = await db.execute(
            select(GovernorCaseRecord).where(GovernorCaseRecord.project_id == uuid.UUID(project_id))
        )
        return res.scalar_one_or_none()

    @staticmethod
    async def list_cases(
        db: AsyncSession,
        limit: int = 50,
        offset: int = 0,
        risk_class: Optional[str] = None,
        recommended_decision: Optional[str] = None,
        pending_reason: Optional[str] = None,
        project_status: Optional[str] = None,
    ) -> tuple[List[GovernorCaseRecord], int]:
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
        case_id: Optional[str],
        project_id: str,
        action_type: str,
        status: str = "executed",
        executed_by: str = "SOFT_CEO",
        result_payload: Optional[Dict] = None,
    ) -> GovernorActionRecord:
        record = GovernorActionRecord(
            case_id=uuid.UUID(case_id) if case_id else None,
            project_id=uuid.UUID(project_id),
            action_type=action_type,
            status=status,
            executed_by=executed_by,
            result_payload=result_payload or {},
        )
        db.add(record)
        await db.flush()
        return record

    @staticmethod
    async def list_actions(
        db: AsyncSession,
        project_id: Optional[str] = None,
        limit: int = 20,
    ) -> List[GovernorActionRecord]:
        q = select(GovernorActionRecord).order_by(GovernorActionRecord.created_at.desc()).limit(limit)
        if project_id:
            q = q.where(GovernorActionRecord.project_id == uuid.UUID(project_id))
        return (await db.execute(q)).scalars().all()


class GovernorEscalationRepo:

    @staticmethod
    async def save_escalation(
        db: AsyncSession,
        case_id: Optional[str],
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
    async def mark_resolved(db: AsyncSession, escalation_id: str) -> bool:
        await db.execute(
            update(GovernorEscalationRecord)
            .where(GovernorEscalationRecord.id == uuid.UUID(escalation_id))
            .values(status="resolved", resolved_at=datetime.now(timezone.utc))
        )
        await db.flush()
        return True

    @staticmethod
    async def list_open(db: AsyncSession, limit: int = 50) -> List[GovernorEscalationRecord]:
        q = (
            select(GovernorEscalationRecord)
            .where(GovernorEscalationRecord.status == "open")
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
