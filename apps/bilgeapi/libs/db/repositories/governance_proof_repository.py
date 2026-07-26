
import uuid

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from bilgeapi.libs.db.models.governance_models import (
    GovernanceProofEventRecord,
    GovernanceProofSnapshotRecord,
    GovernanceProofVerificationRecord,
)


class GovernanceProofEventRepo:
    def __init__(self, db: Session | AsyncSession):
        self.db = db

    def save_event(self, event: GovernanceProofEventRecord) -> GovernanceProofEventRecord:
        if isinstance(self.db, AsyncSession):
            raise RuntimeError("Use save_event_async for AsyncSession")
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    async def save_event_async(self, event: GovernanceProofEventRecord) -> GovernanceProofEventRecord:
        self.db.add(event)
        # Note: We don't commit here if we want transactional integrity with the caller
        await self.db.flush()
        await self.db.refresh(event)
        return event

    def get_last_event(self) -> GovernanceProofEventRecord | None:
        if isinstance(self.db, AsyncSession):
            raise RuntimeError("Use get_last_event_async for AsyncSession")
        return self.db.query(GovernanceProofEventRecord).order_by(desc(GovernanceProofEventRecord.chain_index)).first()

    async def get_last_event_async(self) -> GovernanceProofEventRecord | None:
        result = await self.db.execute(
            select(GovernanceProofEventRecord).order_by(desc(GovernanceProofEventRecord.chain_index)).limit(1)
        )
        return result.scalar_one_or_none()

    def list_events(self, start: int = 0, end: int | None = None) -> list[GovernanceProofEventRecord]:
        if isinstance(self.db, AsyncSession):
            raise RuntimeError("Use list_events_async for AsyncSession")
        query = self.db.query(GovernanceProofEventRecord).filter(GovernanceProofEventRecord.chain_index >= start)
        if end is not None:
            query = query.filter(GovernanceProofEventRecord.chain_index <= end)
        return query.order_by(GovernanceProofEventRecord.chain_index).all()

    async def list_events_async(self, start: int = 0, end: int | None = None) -> list[GovernanceProofEventRecord]:
        query = select(GovernanceProofEventRecord).where(GovernanceProofEventRecord.chain_index >= start)
        if end is not None:
            query = query.where(GovernanceProofEventRecord.chain_index <= end)
        result = await self.db.execute(query.order_by(GovernanceProofEventRecord.chain_index))
        return list(result.scalars().all())


class GovernanceProofSnapshotRepo:
    def __init__(self, db: Session | AsyncSession):
        self.db = db

    def save_snapshot(self, snapshot: GovernanceProofSnapshotRecord) -> GovernanceProofSnapshotRecord:
        if isinstance(self.db, AsyncSession):
            raise RuntimeError("Use save_snapshot_async for AsyncSession")
        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)
        return snapshot

    async def save_snapshot_async(self, snapshot: GovernanceProofSnapshotRecord) -> GovernanceProofSnapshotRecord:
        self.db.add(snapshot)
        await self.db.flush()
        await self.db.refresh(snapshot)
        return snapshot

    def get_snapshot(self, snapshot_id: uuid.UUID) -> GovernanceProofSnapshotRecord | None:
        if isinstance(self.db, AsyncSession):
            raise RuntimeError("Use get_snapshot_async for AsyncSession")
        return self.db.query(GovernanceProofSnapshotRecord).filter(GovernanceProofSnapshotRecord.id == snapshot_id).first()

    async def get_snapshot_async(self, snapshot_id: uuid.UUID) -> GovernanceProofSnapshotRecord | None:
        result = await self.db.execute(
            select(GovernanceProofSnapshotRecord).where(GovernanceProofSnapshotRecord.id == snapshot_id)
        )
        return result.scalar_one_or_none()


class GovernanceVerificationRepo:
    def __init__(self, db: Session | AsyncSession):
        self.db = db

    def save_verification(
        self,
        verification: GovernanceProofVerificationRecord,
    ) -> GovernanceProofVerificationRecord:
        if isinstance(self.db, AsyncSession):
            raise RuntimeError("Use save_verification_async for AsyncSession")
        self.db.add(verification)
        self.db.commit()
        self.db.refresh(verification)
        return verification

    async def save_verification_async(
        self,
        verification: GovernanceProofVerificationRecord,
    ) -> GovernanceProofVerificationRecord:
        self.db.add(verification)
        await self.db.flush()
        await self.db.refresh(verification)
        return verification
