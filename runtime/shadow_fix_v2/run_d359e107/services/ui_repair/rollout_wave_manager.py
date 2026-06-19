import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from libs.db.models.ui_repair_models import UIRolloutWave, UIRepairProjectProfile
from .schemas import UIRolloutWaveCreate

class RolloutWaveManager:
    """Manages staged GA rollout waves."""
    
    @staticmethod
    async def create_wave(db: AsyncSession, data: UIRolloutWaveCreate):
        wave = UIRolloutWave(
            id=uuid.uuid4(),
            wave_name=data.wave_name,
            status="PLANNED",
            project_keys_json=data.project_keys,
            rollout_mode=data.rollout_mode,
            success_criteria_json=data.success_criteria,
            failure_criteria_json=data.failure_criteria,
            created_at=datetime.now(timezone.utc)
        )
        db.add(wave)
        await db.commit()
        await db.refresh(wave)
        return wave

    @staticmethod
    async def start_wave(db: AsyncSession, wave_id: str):
        stmt = select(UIRolloutWave).where(UIRolloutWave.id == uuid.UUID(wave_id))
        res = await db.execute(stmt)
        wave = res.scalar_one_or_none()
        if wave:
            wave.status = "RUNNING"
            wave.started_at = datetime.now(timezone.utc)
            
            # Update all projects in wave to PILOT or ACTIVE depending on mode
            for p_key in (wave.project_keys_json or []):
                stmt_p = select(UIRepairProjectProfile).where(UIRepairProjectProfile.project_key == p_key)
                res_p = await db.execute(stmt_p)
                project = res_p.scalar_one_or_none()
                if project and project.status == "DRAFT":
                    project.status = "PILOT"
            
            await db.commit()
        return wave

    @staticmethod
    async def complete_wave(db: AsyncSession, wave_id: str):
        stmt = select(UIRolloutWave).where(UIRolloutWave.id == uuid.UUID(wave_id))
        res = await db.execute(stmt)
        wave = res.scalar_one_or_none()
        if wave:
            wave.status = "COMPLETED"
            wave.completed_at = datetime.now(timezone.utc)
            
            # Projects move to ACTIVE
            for p_key in (wave.project_keys_json or []):
                stmt_p = select(UIRepairProjectProfile).where(UIRepairProjectProfile.project_key == p_key)
                res_p = await db.execute(stmt_p)
                project = res_p.scalar_one_or_none()
                if project:
                    project.status = "ACTIVE"
                    
            await db.commit()
        return wave

    @staticmethod
    async def list_waves(db: AsyncSession):
        stmt = select(UIRolloutWave).order_by(UIRolloutWave.created_at.desc())
        res = await db.execute(stmt)
        return list(res.scalars().all())
