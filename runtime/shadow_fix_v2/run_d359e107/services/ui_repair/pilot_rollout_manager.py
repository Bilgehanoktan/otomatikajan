import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .pilot_mode import PilotStatus, PilotMode
from libs.db.models.ui_repair_models import UIPilotRollout, UIPilotEvent

class PilotRolloutManager:
    """Orchestrates the start, stop, pause and resume of pilots."""
    
    @staticmethod
    async def start_pilot(db: AsyncSession, name: str, mode: PilotMode, duration: int, created_by: str):
        rollout_id = str(uuid.uuid4())
        rollout = UIPilotRollout(
            id=rollout_id,
            name=name,
            status=PilotStatus.RUNNING.value,
            mode=mode.value if hasattr(mode, 'value') else mode,
            duration_days=duration,
            started_at=datetime.now(timezone.utc),
            created_by=created_by
        )
        db.add(rollout)
        
        event = UIPilotEvent(
            id=str(uuid.uuid4()),
            rollout_id=rollout_id,
            event_type="PILOT_STARTED",
            payload_json={"mode": str(mode), "duration": duration}
        )
        db.add(event)
        await db.commit()
        return rollout

    @staticmethod
    async def pause_pilot(db: AsyncSession, rollout_id: str, rationale: str):
        stmt = select(UIPilotRollout).where(UIPilotRollout.id == rollout_id)
        result = await db.execute(stmt)
        rollout = result.scalar_one_or_none()
        if rollout:
            rollout.status = PilotStatus.PAUSED.value
            event = UIPilotEvent(
                id=str(uuid.uuid4()),
                rollout_id=rollout_id,
                event_type="PILOT_PAUSED",
                payload_json={"rationale": rationale}
            )
            db.add(event)
            await db.commit()
        return rollout

    @staticmethod
    async def stop_pilot(db: AsyncSession, rollout_id: str, rationale: str):
        stmt = select(UIPilotRollout).where(UIPilotRollout.id == rollout_id)
        result = await db.execute(stmt)
        rollout = result.scalar_one_or_none()
        if rollout:
            rollout.status = PilotStatus.COMPLETED.value
            rollout.ended_at = datetime.now(timezone.utc)
            event = UIPilotEvent(
                id=str(uuid.uuid4()),
                rollout_id=rollout_id,
                event_type="PILOT_STOPPED",
                payload_json={"rationale": rationale}
            )
            db.add(event)
            await db.commit()
        return rollout
