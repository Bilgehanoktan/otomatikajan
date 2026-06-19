import inspect
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from libs.db.models.governance_models import (
    GovernorPolicyEvolutionRecord,
    GovernorPolicySimulationRecord,
    GovernorPolicySnapshotRecord,
    PolicyEvolutionStatus,
    PolicyEvolutionType,
)


class GovernorPolicyEvolutionRepo:
    @staticmethod
    async def _execute(db: AsyncSession, stmt):
        result = db.execute(stmt)
        if inspect.isawaitable(result):
            return await result
        return result

    @staticmethod
    async def create_evolution_proposal(
        db: AsyncSession,
        policy_key: str,
        evolution_type: PolicyEvolutionType,
        proposed_value: Any,
        old_value: Any | None = None,
        change_reason: str | None = None,
        evidence_summary: dict | None = None,
        confidence_score: float = 0.0,
        proposed_by: str = "SYSTEM"
    ) -> GovernorPolicyEvolutionRecord:
        record = GovernorPolicyEvolutionRecord(
            policy_key=policy_key,
            evolution_type=evolution_type,
            old_value=old_value,
            proposed_value=proposed_value,
            change_reason=change_reason,
            evidence_summary=evidence_summary,
            confidence_score=confidence_score,
            proposed_by=proposed_by,
            status=PolicyEvolutionStatus.PROPOSED
        )
        db.add(record)
        return record

    @staticmethod
    async def get_evolution(db: AsyncSession, evolution_id: uuid.UUID) -> GovernorPolicyEvolutionRecord | None:
        res = await GovernorPolicyEvolutionRepo._execute(
            db,
            select(GovernorPolicyEvolutionRecord).where(GovernorPolicyEvolutionRecord.id == evolution_id),
        )
        return res.scalar_one_or_none()

    @staticmethod
    async def list_recent_proposals(
        db: AsyncSession,
        limit: int = 50,
        status: PolicyEvolutionStatus | None = None
    ) -> list[GovernorPolicyEvolutionRecord]:
        stmt = select(GovernorPolicyEvolutionRecord).order_by(desc(GovernorPolicyEvolutionRecord.created_at))
        if status:
            stmt = stmt.where(GovernorPolicyEvolutionRecord.status == status)
        res = await GovernorPolicyEvolutionRepo._execute(db, stmt.limit(limit))
        return list(res.scalars().all())

    @staticmethod
    async def update_status(
        db: AsyncSession,
        evolution_id: uuid.UUID,
        status: PolicyEvolutionStatus,
        approved_by: str | None = None
    ) -> bool:
        values = {"status": status}
        if status == PolicyEvolutionStatus.APPLIED:
            values["applied_at"] = datetime.now(UTC)
        if approved_by:
            values["approved_by"] = approved_by

        stmt = update(GovernorPolicyEvolutionRecord).where(GovernorPolicyEvolutionRecord.id == evolution_id).values(**values)
        await GovernorPolicyEvolutionRepo._execute(db, stmt)
        return True


class GovernorPolicySimulationRepo:
    @staticmethod
    async def _execute(db: AsyncSession, stmt):
        result = db.execute(stmt)
        if inspect.isawaitable(result):
            return await result
        return result

    @staticmethod
    async def save_simulation_result(
        db: AsyncSession,
        evolution_id: uuid.UUID,
        window_days: int,
        sample_size: int,
        deltas: dict[str, float],
        result_payload: dict | None = None
    ) -> GovernorPolicySimulationRecord:
        record = GovernorPolicySimulationRecord(
            evolution_id=evolution_id,
            simulation_window_days=window_days,
            sample_size=sample_size,
            predicted_accuracy_delta=deltas.get("accuracy", 0.0),
            predicted_false_positive_delta=deltas.get("false_positive", 0.0),
            predicted_false_negative_delta=deltas.get("false_negative", 0.0),
            predicted_escalation_delta=deltas.get("escalation", 0.0),
            predicted_latency_delta=deltas.get("latency", 0.0),
            result_payload=result_payload
        )
        db.add(record)
        return record

    @staticmethod
    async def get_by_evolution(db: AsyncSession, evolution_id: uuid.UUID) -> list[GovernorPolicySimulationRecord]:
        res = await GovernorPolicySimulationRepo._execute(
            db,
            select(GovernorPolicySimulationRecord)
            .where(GovernorPolicySimulationRecord.evolution_id == evolution_id)
            .order_by(desc(GovernorPolicySimulationRecord.created_at)),
        )
        return list(res.scalars().all())


class GovernorPolicySnapshotRepo:
    @staticmethod
    async def _execute(db: AsyncSession, stmt):
        result = db.execute(stmt)
        if inspect.isawaitable(result):
            return await result
        return result

    @staticmethod
    async def create_policy_snapshot(
        db: AsyncSession,
        snapshot_name: str,
        policy_payload: dict[str, Any],
        created_by: str = "SYSTEM"
    ) -> GovernorPolicySnapshotRecord:
        record = GovernorPolicySnapshotRecord(
            snapshot_name=snapshot_name,
            policy_payload=policy_payload,
            created_by=created_by
        )
        db.add(record)
        return record

    @staticmethod
    async def get_latest_snapshot(db: AsyncSession) -> GovernorPolicySnapshotRecord | None:
        res = await GovernorPolicySnapshotRepo._execute(
            db,
            select(GovernorPolicySnapshotRecord).order_by(desc(GovernorPolicySnapshotRecord.created_at)).limit(1),
        )
        return res.scalar_one_or_none()

    @staticmethod
    async def list_snapshots(db: AsyncSession, limit: int = 20) -> list[GovernorPolicySnapshotRecord]:
        res = await GovernorPolicySnapshotRepo._execute(
            db,
            select(GovernorPolicySnapshotRecord).order_by(desc(GovernorPolicySnapshotRecord.created_at)).limit(limit),
        )
        return list(res.scalars().all())
