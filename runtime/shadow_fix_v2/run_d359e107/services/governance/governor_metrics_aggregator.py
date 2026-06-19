import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from libs.db.models.governance_models import (
    GovernorOutcomeRecord, 
    GovernorDomain, 
    GovernorDecisionQuality,
    GovernorOutcomeType,
    GovernorSloSampleRecord
)
from libs.db.repositories.governor_observability_repository import GovernorMetricAggregateRepo

logger = logging.getLogger(__name__)

class GovernorMetricsAggregator:
    @staticmethod
    async def aggregate_all_metrics(db: AsyncSession, window_minutes: int = 60):
        """Tüm yönetişim metriklerini hesaplar ve kaydeder."""
        logger.info(f"Aggregating governance metrics for last {window_minutes} minutes...")
        
        # 1. Decision Accuracy
        await GovernorMetricsAggregator._aggregate_accuracy(db, window_minutes)
        
        # 2. Conflict Rate
        await GovernorMetricsAggregator._aggregate_conflicts(db, window_minutes)
        
        # 3. Latency (P95)
        await GovernorMetricsAggregator._aggregate_latency(db, window_minutes)

    @staticmethod
    async def _aggregate_accuracy(db: AsyncSession, window_minutes: int):
        since = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
        
        stmt = select(
            func.count(GovernorOutcomeRecord.id).label("total"),
            func.sum(GovernorOutcomeRecord.was_successful).label("success")
        ).where(GovernorOutcomeRecord.created_at >= since)
        
        res = await db.execute(stmt)
        row = res.one()
        total = row.total or 0
        success = row.success or 0
        
        accuracy = (success / total) if total > 0 else 1.0
        
        await GovernorMetricAggregateRepo.save_metric_aggregate(
            db, "decision_accuracy", accuracy, window_minutes=window_minutes, sample_size=total
        )

    @staticmethod
    async def _aggregate_conflicts(db: AsyncSession, window_minutes: int):
        # Conflict rate metrikleri (Meta tabanlı)
        pass

    @staticmethod
    async def _aggregate_latency(db: AsyncSession, window_minutes: int):
        since = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
        
        stmt = select(func.avg(GovernorSloSampleRecord.latency_ms)).where(
            GovernorSloSampleRecord.created_at >= since
        )
        res = await db.execute(stmt)
        avg_latency = res.scalar() or 0
        
        await GovernorMetricAggregateRepo.save_metric_aggregate(
            db, "avg_decision_latency", float(avg_latency), window_minutes=window_minutes
        )
