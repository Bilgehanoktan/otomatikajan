import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy import select, desc, update
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.governance_models import (
    GovernorPolicyEvolutionRecord, 
    GovernorPolicySimulationRecord, 
    GovernorPolicySnapshotRecord,
    PolicyEvolutionStatus,
    PolicyEvolutionType
)

class GovernorPolicyEvolutionRepo:
    @staticmethod
    async def create_evolution_proposal(
        db: AsyncSession,
        policy_key: str,
        evolution_type: PolicyEvolutionType,
        proposed_value: Any,
        old_value: Optional[Any] = None,
        change_reason: Optional[str] = None,
        evidence_summary: Optional[Dict] = None,
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
    async def get_evolution(db: AsyncSession, evolution_id: uuid.UUID) -> Optional[GovernorPolicyEvolutionRecord]:
        res = await db.execute(select(GovernorPolicyEvolutionRecord).where(GovernorPolicyEvolutionRecord.id == evolution_id))
        return res.scalar_one_or_none()

    @staticmethod
    async def list_recent_proposals(
        db: AsyncSession, 
        limit: int = 50,
        status: Optional[PolicyEvolutionStatus] = None
    ) -> List[GovernorPolicyEvolutionRecord]:
        stmt = select(GovernorPolicyEvolutionRecord).order_by(desc(GovernorPolicyEvolutionRecord.created_at))
        if status:
            stmt = stmt.where(GovernorPolicyEvolutionRecord.status == status)
        res = await db.execute(stmt.limit(limit))
        return list(res.scalars().all())

    @staticmethod
    async def update_status(
        db: AsyncSession, 
        evolution_id: uuid.UUID, 
        status: PolicyEvolutionStatus,
        approved_by: Optional[str] = None
    ) -> bool:
        values = {"status": status}
        if status == PolicyEvolutionStatus.APPLIED:
            values["applied_at"] = datetime.now(timezone.utc)
        if approved_by:
            values["approved_by"] = approved_by
            
        stmt = update(GovernorPolicyEvolutionRecord).where(GovernorPolicyEvolutionRecord.id == evolution_id).values(**values)
        await db.execute(stmt)
        return True


class GovernorPolicySimulationRepo:
    @staticmethod
    async def save_simulation_result(
        db: AsyncSession,
        evolution_id: uuid.UUID,
        window_days: int,
        sample_size: int,
        deltas: Dict[str, float],
        result_payload: Optional[Dict] = None
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
    async def get_by_evolution(db: AsyncSession, evolution_id: uuid.UUID) -> List[GovernorPolicySimulationRecord]:
        res = await db.execute(
            select(GovernorPolicySimulationRecord)
            .where(GovernorPolicySimulationRecord.evolution_id == evolution_id)
            .order_by(desc(GovernorPolicySimulationRecord.created_at))
        )
        return list(res.scalars().all())


class GovernorPolicySnapshotRepo:
    @staticmethod
    async def create_policy_snapshot(
        db: AsyncSession,
        snapshot_name: str,
        policy_payload: Dict[str, Any],
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
    async def get_latest_snapshot(db: AsyncSession) -> Optional[GovernorPolicySnapshotRecord]:
        res = await db.execute(select(GovernorPolicySnapshotRecord).order_by(desc(GovernorPolicySnapshotRecord.created_at)).limit(1))
        return res.scalar_one_or_none()

    @staticmethod
    async def list_snapshots(db: AsyncSession, limit: int = 20) -> List[GovernorPolicySnapshotRecord]:
        res = await db.execute(select(GovernorPolicySnapshotRecord).order_by(desc(GovernorPolicySnapshotRecord.created_at)).limit(limit))
        return list(res.scalars().all())
