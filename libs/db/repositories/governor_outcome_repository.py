"""
Soft CEO — Governor Outcome Repository Layer (Faz 5)
Performance tracking and scorecard data provider.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

import sqlalchemy as sa
from sqlalchemy import select, func, and_, desc, case
from sqlalchemy.ext.asyncio import AsyncSession

from libs.db.models.governance_models import (
    GovernorOutcomeRecord, GovernorOutcomeType, GovernorOutcomeQuality
)
from services.observability.logging import get_logger

logger = get_logger("db.governor_outcome_repo")

class GovernorOutcomeRepo:

    @staticmethod
    async def create_outcome(db: AsyncSession, data: Dict[str, Any]) -> GovernorOutcomeRecord:
        record = GovernorOutcomeRecord(**data)
        db.add(record)
        await db.flush()
        return record

    @staticmethod
    async def get_by_case(db: AsyncSession, case_id: uuid.UUID) -> Optional[GovernorOutcomeRecord]:
        res = await db.execute(
            select(GovernorOutcomeRecord).where(GovernorOutcomeRecord.case_id == case_id)
        )
        return res.scalar_one_or_none()

    @staticmethod
    async def list_recent(db: AsyncSession, limit: int = 50, offset: int = 0) -> List[GovernorOutcomeRecord]:
        res = await db.execute(
            select(GovernorOutcomeRecord)
            .order_by(desc(GovernorOutcomeRecord.created_at))
            .limit(limit)
            .offset(offset)
        )
        return list(res.scalars().all())

    @staticmethod
    async def list_by_project(db: AsyncSession, project_id: uuid.UUID) -> List[GovernorOutcomeRecord]:
        res = await db.execute(
            select(GovernorOutcomeRecord)
            .where(GovernorOutcomeRecord.project_id == project_id)
            .order_by(desc(GovernorOutcomeRecord.created_at))
        )
        return list(res.scalars().all())

    @staticmethod
    async def aggregate_metrics(db: AsyncSession, window_days: int = 7) -> Dict[str, Any]:
        since = datetime.now(timezone.utc) - timedelta(days=window_days)
        
        # Total counts
        total_res = await db.execute(
            select(func.count(GovernorOutcomeRecord.id))
            .where(GovernorOutcomeRecord.created_at >= since)
        )
        total = total_res.scalar() or 0
        
        # Accuracy
        correct_res = await db.execute(
            select(func.count(GovernorOutcomeRecord.id))
            .where(and_(
                GovernorOutcomeRecord.created_at >= since,
                GovernorOutcomeRecord.quality == GovernorOutcomeQuality.OPTIMAL
            ))
        )
        correct = correct_res.scalar() or 0
        
        # Replay success rate
        replay_total_res = await db.execute(
            select(func.count(GovernorOutcomeRecord.id))
            .where(and_(
                GovernorOutcomeRecord.created_at >= since,
                GovernorOutcomeRecord.decision == "AUTO_REPLAY_CANDIDATE"
            ))
        )
        replay_total = replay_total_res.scalar() or 0
        
        replay_success_res = await db.execute(
            select(func.count(GovernorOutcomeRecord.id))
            .where(and_(
                GovernorOutcomeRecord.created_at >= since,
                GovernorOutcomeRecord.decision == "AUTO_REPLAY_CANDIDATE",
                GovernorOutcomeRecord.final_outcome == GovernorOutcomeType.SUCCESS
            ))
        )
        replay_success = replay_success_res.scalar() or 0
        
        # Latency
        latency_res = await db.execute(
            select(func.avg(GovernorOutcomeRecord.resolution_latency_seconds))
            .where(GovernorOutcomeRecord.created_at >= since)
        )
        avg_latency = latency_res.scalar() or 0

        # Operator Agreement
        agreed_res = await db.execute(
            select(func.count(GovernorOutcomeRecord.id))
            .where(and_(
                GovernorOutcomeRecord.created_at >= since,
                GovernorOutcomeRecord.operator_agreed == 1
            ))
        )
        agreed = agreed_res.scalar() or 0

        return {
            "total_decisions": total,
            "correct_decisions": correct,
            "accuracy": (correct / total * 100) if total > 0 else 0,
            "replay_success_rate": (replay_success / replay_total * 100) if replay_total > 0 else 0,
            "avg_latency_seconds": float(avg_latency) if avg_latency else 0,
            "agreement_rate": (agreed / total * 100) if total > 0 else 0,
            "total_agreed": agreed
        }

    @staticmethod
    async def aggregate_by_decision(db: AsyncSession, window_days: int = 7) -> List[Dict[str, Any]]:
        since = datetime.now(timezone.utc) - timedelta(days=window_days)
        res = await db.execute(
            select(
                GovernorOutcomeRecord.decision,
                func.count(GovernorOutcomeRecord.id).label("total"),
                func.sum(case((GovernorOutcomeRecord.quality == GovernorOutcomeQuality.OPTIMAL, 1), else_=0)).label("correct")
            )
            .where(GovernorOutcomeRecord.created_at >= since)
            .group_by(GovernorOutcomeRecord.decision)
        )
        
        results = []
        for row in res:
            results.append({
                "decision": row.decision,
                "total": row.total,
                "correct": int(row.correct or 0),
                "accuracy": (int(row.correct or 0) / row.total * 100) if row.total > 0 else 0
            })
        return results
