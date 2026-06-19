import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from libs.db.models.ui_repair_models import UISLOBreach
from .schemas import UISLOBreachCreate

class SLOBreachManager:
    @staticmethod
    async def list_breaches(db: AsyncSession, project_key: Optional[str] = None) -> List[UISLOBreach]:
        stmt = select(UISLOBreach)
        if project_key:
            stmt = stmt.where(UISLOBreach.project_key == project_key)
        result = await db.execute(stmt.order_by(UISLOBreach.created_at.desc()))
        return list(result.scalars().all())

    @staticmethod
    async def create_breach(db: AsyncSession, data: UISLOBreachCreate) -> UISLOBreach:
        breach = UISLOBreach(
            id=uuid.uuid4(),
            project_key=data.project_key,
            slo_name=data.slo_name,
            severity=data.severity,
            observed_value=data.observed_value,
            target_value=data.target_value,
            breach_started_at=data.breach_started_at,
            status=data.status,
            linked_incident_id=data.linked_incident_id,
            remediation_plan_json=data.remediation_plan
        )
        db.add(breach)
        await db.commit()
        await db.refresh(breach)
        return breach

    @staticmethod
    async def resolve_breach(db: AsyncSession, breach_id: str) -> Optional[UISLOBreach]:
        result = await db.execute(select(UISLOBreach).where(UISLOBreach.id == breach_id))
        breach = result.scalar_one_or_none()
        if breach:
            breach.status = "RESOLVED"
            breach.breach_resolved_at = datetime.now(timezone.utc)
            await db.commit()
            await db.refresh(breach)
        return breach
        
    @staticmethod
    async def acknowledge_breach(db: AsyncSession, breach_id: str) -> Optional[UISLOBreach]:
        result = await db.execute(select(UISLOBreach).where(UISLOBreach.id == breach_id))
        breach = result.scalar_one_or_none()
        if breach:
            breach.status = "ACKNOWLEDGED"
            await db.commit()
            await db.refresh(breach)
        return breach
