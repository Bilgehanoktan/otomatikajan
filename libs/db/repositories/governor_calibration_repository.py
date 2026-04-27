"""
Soft CEO — Governor Calibration Repository Layer (Faz 6)
Adaptive threshold persistence and management.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import sqlalchemy as sa
from sqlalchemy import select, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from libs.db.models.governance_models import (
    GovernorCalibrationRecord, CalibrationStatus
)
from services.observability.logging import get_logger

logger = get_logger("db.governor_calibration_repo")

class GovernorCalibrationRepo:

    @staticmethod
    async def create_proposal(db: AsyncSession, data: Dict[str, Any]) -> GovernorCalibrationRecord:
        record = GovernorCalibrationRecord(**data)
        record.status = CalibrationStatus.PROPOSED
        db.add(record)
        await db.flush()
        return record

    @staticmethod
    async def list_recent(db: AsyncSession, limit: int = 50) -> List[GovernorCalibrationRecord]:
        res = await db.execute(
            select(GovernorCalibrationRecord)
            .order_by(desc(GovernorCalibrationRecord.created_at))
            .limit(limit)
        )
        return list(res.scalars().all())

    @staticmethod
    async def get_active_value(db: AsyncSession, parameter_name: str) -> Optional[float]:
        """En son APPLIED olan değeri döner."""
        res = await db.execute(
            select(GovernorCalibrationRecord.applied_value)
            .where(and_(
                GovernorCalibrationRecord.parameter_name == parameter_name,
                GovernorCalibrationRecord.status == CalibrationStatus.APPLIED
            ))
            .order_by(desc(GovernorCalibrationRecord.applied_at))
            .limit(1)
        )
        return res.scalar()

    @staticmethod
    async def get_by_id(db: AsyncSession, calibration_id: uuid.UUID) -> Optional[GovernorCalibrationRecord]:
        res = await db.execute(
            select(GovernorCalibrationRecord).where(GovernorCalibrationRecord.id == calibration_id)
        )
        return res.scalar_one_or_none()

    @staticmethod
    async def apply_calibration(db: AsyncSession, calibration_id: uuid.UUID, approved_by: str) -> bool:
        record = await GovernorCalibrationRepo.get_by_id(db, calibration_id)
        if not record or record.status != CalibrationStatus.PROPOSED:
            return False
            
        record.status = CalibrationStatus.APPLIED
        record.approved_by = approved_by
        record.applied_value = record.proposed_value
        record.applied_at = datetime.now(timezone.utc)
        
        await db.flush()
        return True

    @staticmethod
    async def reject_calibration(db: AsyncSession, calibration_id: uuid.UUID, approved_by: str, reason: str) -> bool:
        record = await GovernorCalibrationRepo.get_by_id(db, calibration_id)
        if not record or record.status != CalibrationStatus.PROPOSED:
            return False
            
        record.status = CalibrationStatus.REJECTED
        record.approved_by = approved_by
        record.change_reason = f"{record.change_reason or ''} | REJECTED: {reason}"
        
        await db.flush()
        return True

    @staticmethod
    async def rollback_calibration(db: AsyncSession, calibration_id: uuid.UUID, approved_by: str, reason: str) -> bool:
        record = await GovernorCalibrationRepo.get_by_id(db, calibration_id)
        if not record or record.status != CalibrationStatus.APPLIED:
            return False
            
        record.status = CalibrationStatus.ROLLED_BACK
        record.approved_by = approved_by
        record.change_reason = f"{record.change_reason or ''} | ROLLED_BACK: {reason}"
        
        await db.flush()
        return True
