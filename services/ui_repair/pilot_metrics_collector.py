import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from libs.db.models.ui_repair_models import UIPilotMetrics, UIPilotEvent

class PilotMetricsCollector:
    """Collects and aggregates metrics during the pilot rollout."""
    
    @staticmethod
    async def get_metrics(db: AsyncSession, rollout_id: str):
        stmt = select(UIPilotMetrics).where(UIPilotMetrics.rollout_id == rollout_id)
        result = await db.execute(stmt)
        metrics = result.scalar_one_or_none()
        if not metrics:
            # Initialize metrics if not exists
            metrics = UIPilotMetrics(id=str(uuid.uuid4()), rollout_id=rollout_id)
            db.add(metrics)
            await db.commit()
            await db.refresh(metrics)
        return metrics

    @staticmethod
    async def record_event(db: AsyncSession, rollout_id: str, event_type: str, payload: Optional[dict] = None):
        event = UIPilotEvent(
            id=str(uuid.uuid4()),
            rollout_id=rollout_id,
            event_type=event_type,
            payload_json=payload or {}
        )
        db.add(event)
        
        # Update metrics count based on event type
        metrics = await PilotMetricsCollector.get_metrics(db, rollout_id)
        if event_type == "MONITOR_RUN":
            metrics.monitoring_runs += 1
        elif event_type == "FAILURE_DETECTED":
            metrics.failures_detected += 1
        elif event_type == "PR_CREATED":
            metrics.prs_created += 1
        elif event_type == "APPLY_APPROVED":
            metrics.approved_applies += 1
        elif event_type == "OPERATOR_ACTION":
            metrics.operator_actions_count += 1
            
        await db.commit()
