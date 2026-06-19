import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.ui_repair_models import UICapacityForecast
from .workload_forecaster import WorkloadForecaster

class CapacityPlanner:
    """Plans resource capacity based on workload forecasts."""
    
    @staticmethod
    async def generate_capacity_plan(db: AsyncSession, project_key: str) -> UICapacityForecast:
        """Generate and save a capacity forecast for a project."""
        forecast_data = await WorkloadForecaster.get_forecast(db, project_key, window_days=30)
        
        # Translate workload to capacity requirements
        plan = UICapacityForecast(
            id=uuid.uuid4(),
            project_key=project_key,
            forecast_window="30D",
            expected_monitoring_runs=forecast_data["projected_ops"].get("MONITORING_RUN", 0),
            expected_repair_attempts=forecast_data["projected_ops"].get("OPENSWE_REPAIR", 0),
            expected_verifier_runs=forecast_data["projected_ops"].get("VERIFIER_MESH_RUN", 0),
            expected_llm_calls=sum(forecast_data["projected_ops"].values()),
            expected_cost_usd=forecast_data["projected_cost"],
            confidence=forecast_data["confidence"],
            created_at=datetime.now(timezone.utc)
        )
        
        db.add(plan)
        await db.commit()
        await db.refresh(plan)
        return plan

    @staticmethod
    async def get_latest_plan(db: AsyncSession, project_key: str) -> Optional[UICapacityForecast]:
        from sqlalchemy import select
        stmt = select(UICapacityForecast).where(
            UICapacityForecast.project_key == project_key
        ).order_by(UICapacityForecast.created_at.desc()).limit(1)
        
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
