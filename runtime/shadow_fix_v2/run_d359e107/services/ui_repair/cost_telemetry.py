import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from libs.db.models.ui_repair_models import UICostEvent
from .schemas import UICostEventCreate

class CostTelemetry:
    """Service for recording and retrieving granular operational costs."""
    
    @staticmethod
    async def record_event(db: AsyncSession, data: UICostEventCreate) -> UICostEvent:
        """Record a single cost event (LLM call, tool execution, etc)."""
        # Ensure we don't save raw secrets (simple check)
        metadata = data.metadata.copy()
        if "api_key" in metadata:
            metadata["api_key"] = "***REDACTED***"
            
        event = UICostEvent(
            id=uuid.uuid4(),
            project_key=data.project_key,
            team_key=data.team_key,
            source_type=data.source_type,
            source_id=data.source_id,
            operation_type=data.operation_type,
            provider=data.provider,
            model=data.model,
            input_tokens=data.input_tokens,
            output_tokens=data.output_tokens,
            tool_calls=data.tool_calls,
            duration_ms=data.duration_ms,
            estimated_cost_usd=data.estimated_cost_usd,
            metadata_json=metadata,
            created_at=datetime.now(timezone.utc)
        )
        db.add(event)
        await db.commit()
        await db.refresh(event)
        return event

    @staticmethod
    async def get_total_cost(
        db: AsyncSession, 
        project_key: Optional[str] = None,
        team_key: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> float:
        """Calculate total estimated cost for a given scope and time range."""
        stmt = select(func.sum(UICostEvent.estimated_cost_usd))
        if project_key:
            stmt = stmt.where(UICostEvent.project_key == project_key)
        if team_key:
            stmt = stmt.where(UICostEvent.team_key == team_key)
        if since:
            stmt = stmt.where(UICostEvent.created_at >= since)
            
        result = await db.execute(stmt)
        return result.scalar() or 0.0

    @staticmethod
    async def list_events(
        db: AsyncSession, 
        project_key: Optional[str] = None,
        limit: int = 100
    ) -> List[UICostEvent]:
        """List recent cost events."""
        stmt = select(UICostEvent).order_by(UICostEvent.created_at.desc()).limit(limit)
        if project_key:
            stmt = stmt.where(UICostEvent.project_key == project_key)
            
        result = await db.execute(stmt)
        return list(result.scalars().all())
