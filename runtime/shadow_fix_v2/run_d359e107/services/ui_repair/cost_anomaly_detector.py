import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from libs.db.models.ui_repair_models import UICostEvent, UICostAnomaly

class CostAnomalyDetector:
    """Detects unusual operational cost patterns."""
    
    @staticmethod
    async def detect_anomalies(db: AsyncSession, project_key: str) -> List[UICostAnomaly]:
        """Detect anomalies in the last 24 hours compared to previous 7 days average."""
        now = datetime.now(timezone.utc)
        last_24h_start = now - timedelta(days=1)
        prev_week_start = now - timedelta(days=8)
        
        # 1. Get average daily cost over previous 7 days
        stmt_avg = select(func.sum(UICostEvent.estimated_cost_usd)).where(
            UICostEvent.project_key == project_key,
            UICostEvent.created_at >= prev_week_start,
            UICostEvent.created_at < last_24h_start
        )
        result_avg = await db.execute(stmt_avg)
        total_prev_cost = result_avg.scalar() or 0.0
        avg_daily_cost = total_prev_cost / 7.0
        
        # 2. Get cost in last 24 hours
        stmt_last = select(func.sum(UICostEvent.estimated_cost_usd)).where(
            UICostEvent.project_key == project_key,
            UICostEvent.created_at >= last_24h_start
        )
        result_last = await db.execute(stmt_last)
        last_24h_cost = result_last.scalar() or 0.0
        
        anomalies = []
        
        # Threshold: 200% of average daily cost and at least $5
        if last_24h_cost > max(avg_daily_cost * 2, 5.0):
            deviation = ((last_24h_cost - avg_daily_cost) / avg_daily_cost * 100) if avg_daily_cost > 0 else 100
            
            anomaly = UICostAnomaly(
                id=uuid.uuid4(),
                project_key=project_key,
                anomaly_type="COST_SPIKE",
                severity="HIGH" if deviation > 300 else "MEDIUM",
                observed_cost_usd=last_24h_cost,
                expected_cost_usd=avg_daily_cost,
                deviation_percent=deviation,
                reason=f"Sudden cost spike: ${last_24h_cost:.2f} (Expected avg: ${avg_daily_cost:.2f})",
                status="OPEN",
                created_at=now
            )
            db.add(anomaly)
            anomalies.append(anomaly)
            
        # 3. Detect repetitive failure loops (expensive ones)
        # Simplified logic for now
        
        if anomalies:
            await db.commit()
            for a in anomalies:
                await db.refresh(a)
                
        return anomalies

    @staticmethod
    async def list_anomalies(db: AsyncSession, project_key: Optional[str] = None) -> List[UICostAnomaly]:
        stmt = select(UICostAnomaly).order_by(UICostAnomaly.created_at.desc())
        if project_key:
            stmt = stmt.where(UICostAnomaly.project_key == project_key)
        result = await db.execute(stmt)
        return list(result.scalars().all())
        
    @staticmethod
    async def resolve_anomaly(db: AsyncSession, anomaly_id: str) -> Optional[UICostAnomaly]:
        stmt = select(UICostAnomaly).where(UICostAnomaly.id == anomaly_id)
        result = await db.execute(stmt)
        anomaly = result.scalar_one_or_none()
        if anomaly:
            anomaly.status = "RESOLVED"
            anomaly.resolved_at = datetime.now(timezone.utc)
            await db.commit()
            await db.refresh(anomaly)
        return anomaly
