"""
Sovereign AGI — Phase 31
services/governance/learning_repository.py
Repository for accessing learning records, fingerprints and strategy memory.
"""

import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.learning_models import ErrorFingerprint, LearningRecord, StrategyMemory, NegativePatternMemory

class LearningRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_fingerprints(self, limit: int = 50, offset: int = 0) -> List[ErrorFingerprint]:
        stmt = select(ErrorFingerprint).order_by(desc(ErrorFingerprint.last_seen_at)).limit(limit).offset(offset)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_fingerprint_detail(self, fp_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        stmt = select(ErrorFingerprint).where(ErrorFingerprint.id == fp_id)
        res = await self.db.execute(stmt)
        fp = res.scalar_one_or_none()
        if not fp:
            return None
            
        # Get related records
        rec_stmt = select(LearningRecord).where(LearningRecord.fingerprint_id == fp_id).order_by(desc(LearningRecord.created_at)).limit(10)
        rec_res = await self.db.execute(rec_stmt)
        records = rec_res.scalars().all()
        
        # Get strategy memory
        strat_stmt = select(StrategyMemory).where(
            StrategyMemory.component == fp.component,
            StrategyMemory.error_family == fp.error_family
        )
        strat_res = await self.db.execute(strat_stmt)
        strategies = strat_res.scalars().all()
        
        return {
            "fingerprint": fp,
            "recent_records": records,
            "strategies": strategies
        }

    async def get_learning_records(self, limit: int = 50, offset: int = 0) -> List[LearningRecord]:
        stmt = select(LearningRecord).order_by(desc(LearningRecord.created_at)).limit(limit).offset(offset)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_strategy_memory(self) -> List[StrategyMemory]:
        stmt = select(StrategyMemory).order_by(desc(StrategyMemory.trust_score))
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_negative_patterns(self) -> List[NegativePatternMemory]:
        stmt = select(NegativePatternMemory).order_by(desc(NegativePatternMemory.penalty_weight))
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_adaptation_candidates(self) -> List[StrategyMemory]:
        """State'i 'candidate' olan ve 'trusted' olmaya yakın olanları döner."""
        stmt = select(StrategyMemory).where(StrategyMemory.state == "candidate").order_by(desc(StrategyMemory.trust_score))
        res = await self.db.execute(stmt)
        return list(res.scalars().all())
