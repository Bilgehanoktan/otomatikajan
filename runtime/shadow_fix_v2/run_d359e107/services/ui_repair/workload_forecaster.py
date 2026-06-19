from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from libs.db.models.ui_repair_models import UICostEvent

class WorkloadForecaster:
    """Predicts future workload volume based on historical trends."""
    
    @staticmethod
    async def get_forecast(db: AsyncSession, project_key: str, window_days: int = 30) -> Dict[str, Any]:
        """Simple linear extrapolation of workload."""
        now = datetime.now(timezone.utc)
        since = now - timedelta(days=window_days)
        
        # Get historical volumes
        stmt = select(
            UICostEvent.operation_type,
            func.count(UICostEvent.id).label("total_count"),
            func.sum(UICostEvent.estimated_cost_usd).label("total_cost")
        ).where(
            UICostEvent.project_key == project_key,
            UICostEvent.created_at >= since
        ).group_by(UICostEvent.operation_type)
        
        result = await db.execute(stmt)
        history = {r.operation_type: {"count": r.total_count, "cost": r.total_cost} for r in result.all()}
        
        # Simple projection (assuming same rate for next window_days)
        forecast = {
            "window_days": window_days,
            "projected_ops": {},
            "projected_cost": 0.0,
            "confidence": 0.8 # Static for now
        }
        
        for op, data in history.items():
            forecast["projected_ops"][op] = data["count"]
            forecast["projected_cost"] += (data["cost"] or 0.0)
            
        return forecast
