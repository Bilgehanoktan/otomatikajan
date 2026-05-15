from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from libs.db.models.ui_repair_models import UICostEvent

class CostAttributionService:
    """Aggregates cost data by project, team, and operation type."""
    
    @staticmethod
    async def get_project_attribution(db: AsyncSession, days: int = 30) -> List[Dict[str, Any]]:
        """Get cost breakdown by project."""
        since = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = select(
            UICostEvent.project_key,
            func.sum(UICostEvent.estimated_cost_usd).label("total_cost"),
            func.count(UICostEvent.id).label("event_count")
        ).where(UICostEvent.created_at >= since).group_by(UICostEvent.project_key)
        
        result = await db.execute(stmt)
        return [
            {
                "project_key": r.project_key,
                "total_cost": r.total_cost,
                "event_count": r.event_count
            } for r in result.all()
        ]

    @staticmethod
    async def get_team_attribution(db: AsyncSession, days: int = 30) -> List[Dict[str, Any]]:
        """Get cost breakdown by team."""
        since = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = select(
            UICostEvent.team_key,
            func.sum(UICostEvent.estimated_cost_usd).label("total_cost"),
            func.count(UICostEvent.id).label("event_count")
        ).where(UICostEvent.created_at >= since).group_by(UICostEvent.team_key)
        
        result = await db.execute(stmt)
        return [
            {
                "team_key": r.team_key or "UNASSIGNED",
                "total_cost": r.total_cost,
                "event_count": r.event_count
            } for r in result.all()
        ]

    @staticmethod
    async def get_operation_attribution(db: AsyncSession, days: int = 30) -> List[Dict[str, Any]]:
        """Get cost breakdown by operation type."""
        since = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = select(
            UICostEvent.operation_type,
            func.sum(UICostEvent.estimated_cost_usd).label("total_cost"),
            func.count(UICostEvent.id).label("event_count")
        ).where(UICostEvent.created_at >= since).group_by(UICostEvent.operation_type)
        
        result = await db.execute(stmt)
        return [
            {
                "operation_type": r.operation_type,
                "total_cost": r.total_cost,
                "event_count": r.event_count
            } for r in result.all()
        ]

    @staticmethod
    async def get_repair_cost_metrics(db: AsyncSession, project_key: str) -> Dict[str, Any]:
        """Specific metrics for repair operations."""
        # Cost per repair attempt
        # Cost per successful repair (would need joining with cases, but for now aggregate)
        stmt = select(
            func.avg(UICostEvent.estimated_cost_usd).label("avg_cost"),
            func.max(UICostEvent.estimated_cost_usd).label("max_cost"),
            func.sum(UICostEvent.estimated_cost_usd).label("total_cost")
        ).where(
            UICostEvent.project_key == project_key,
            UICostEvent.operation_type == "OPENSWE_REPAIR"
        )
        
        result = await db.execute(stmt)
        row = result.one()
        return {
            "avg_cost_per_repair": row.avg_cost or 0.0,
            "max_cost_single_repair": row.max_cost or 0.0,
            "total_repair_spend": row.total_cost or 0.0
        }
