import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from bilgeapi.libs.db.models.governance_models import (
    GovernorCircuitBreakerRecord,
    GovernorDomain,
    GovernorDrillRecord,
    GovernorDrillStatus,
    GovernorDrillType,
    GovernorRuntimeRecord,
    GovernorRuntimeStatus,
    GovernorSloSampleRecord,
)


class GovernorResilienceRepo:
    @staticmethod
    async def upsert_runtime_status(
        db: AsyncSession,
        domain: GovernorDomain,
        status: GovernorRuntimeStatus,
        reason: str | None = None,
        freeze_mode: int = 0,
        advisory_only: int = 0
    ) -> GovernorRuntimeRecord:
        """Domain runtime durumunu günceller veya oluşturur."""
        stmt = select(GovernorRuntimeRecord).where(GovernorRuntimeRecord.domain == domain)
        result = await db.execute(stmt)
        record = result.scalar_one_or_none()

        now = datetime.now(UTC)

        if record:
            record.runtime_status = status
            record.reason = reason
            record.freeze_mode = freeze_mode
            record.advisory_only = advisory_only
            record.updated_at = now
            if status == GovernorRuntimeStatus.HEALTHY:
                record.last_healthy_at = now
                record.failure_count = 0
            else:
                record.last_failure_at = now
                record.failure_count += 1
        else:
            record = GovernorRuntimeRecord(
                domain=domain,
                runtime_status=status,
                reason=reason,
                freeze_mode=freeze_mode,
                advisory_only=advisory_only,
                last_healthy_at=now if status == GovernorRuntimeStatus.HEALTHY else None,
                last_failure_at=now if status != GovernorRuntimeStatus.HEALTHY else None,
                failure_count=1 if status != GovernorRuntimeStatus.HEALTHY else 0
            )
            db.add(record)

        await db.commit()
        await db.refresh(record)
        return record

    @staticmethod
    async def get_runtime_status(db: AsyncSession, domain: GovernorDomain) -> GovernorRuntimeRecord | None:
        stmt = select(GovernorRuntimeRecord).where(GovernorRuntimeRecord.domain == domain)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

class GovernorDrillRepo:
    @staticmethod
    async def record_drill(
        db: AsyncSession,
        drill_type: GovernorDrillType,
        target_domain: GovernorDomain | None = None,
        scenario_payload: dict[str, Any] | None = None,
        created_by: str = "SYSTEM"
    ) -> GovernorDrillRecord:
        record = GovernorDrillRecord(
            drill_type=drill_type,
            target_domain=target_domain,
            status=GovernorDrillStatus.PLANNED,
            scenario_payload=scenario_payload,
            created_by=created_by
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return record

    @staticmethod
    async def update_drill_status(
        db: AsyncSession,
        drill_id: uuid.UUID,
        status: GovernorDrillStatus,
        result_payload: dict[str, Any] | None = None
    ) -> GovernorDrillRecord | None:
        stmt = select(GovernorDrillRecord).where(GovernorDrillRecord.id == drill_id)
        result = await db.execute(stmt)
        record = result.scalar_one_or_none()

        if record:
            record.status = status
            record.result_payload = result_payload
            if status == GovernorDrillStatus.RUNNING:
                record.started_at = datetime.now(UTC)
            elif status in [GovernorDrillStatus.PASSED, GovernorDrillStatus.FAILED, GovernorDrillStatus.ABORTED]:
                record.completed_at = datetime.now(UTC)

            await db.commit()
            await db.refresh(record)
        return record

class GovernorSloRepo:
    @staticmethod
    async def save_slo_sample(
        db: AsyncSession,
        domain: GovernorDomain,
        operation_name: str,
        latency_ms: int,
        success: bool = True
    ) -> GovernorSloSampleRecord:
        record = GovernorSloSampleRecord(
            domain=domain,
            operation_name=operation_name,
            latency_ms=latency_ms,
            success=1 if success else 0
        )
        db.add(record)
        await db.commit()
        return record

    @staticmethod
    async def list_recent_slo(db: AsyncSession, domain: GovernorDomain, limit: int = 100) -> list[GovernorSloSampleRecord]:
        stmt = select(GovernorSloSampleRecord).where(
            GovernorSloSampleRecord.domain == domain
        ).order_by(desc(GovernorSloSampleRecord.created_at)).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

class GovernorCircuitBreakerRepo:
    @staticmethod
    async def upsert_circuit_state(
        db: AsyncSession,
        domain: GovernorDomain,
        state: str,
        reason: str | None = None
    ) -> GovernorCircuitBreakerRecord:
        stmt = select(GovernorCircuitBreakerRecord).where(GovernorCircuitBreakerRecord.domain == domain)
        result = await db.execute(stmt)
        record = result.scalar_one_or_none()

        now = datetime.now(UTC)
        if record:
            record.state = state
            record.trigger_reason = reason
            if state == "OPEN":
                record.opened_at = now
            elif state == "CLOSED":
                record.closed_at = now
        else:
            record = GovernorCircuitBreakerRecord(
                domain=domain,
                state=state,
                trigger_reason=reason,
                opened_at=now if state == "OPEN" else None,
                closed_at=now if state == "CLOSED" else None
            )
            db.add(record)

        await db.commit()
        await db.refresh(record)
        return record

    @staticmethod
    async def get_circuit_state(db: AsyncSession, domain: GovernorDomain) -> GovernorCircuitBreakerRecord | None:
        stmt = select(GovernorCircuitBreakerRecord).where(GovernorCircuitBreakerRecord.domain == domain)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
