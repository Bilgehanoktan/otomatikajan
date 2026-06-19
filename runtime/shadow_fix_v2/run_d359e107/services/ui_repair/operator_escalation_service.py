from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from libs.db.models.ui_repair_models import UIOperatorEscalation, UINotificationDelivery
from .notification_adapter import NotificationAdapter

class EscalationPolicy:
    """Rules for determining when and how to escalate failures."""
    
    @staticmethod
    def get_severity(failure_type: str, route: str, count: int) -> str:
        if "CRITICAL" in failure_type or "AUTH" in route.upper():
            return "CRITICAL"
        if count >= 5:
            return "URGENT"
        if count >= 3:
            return "OPERATOR_REVIEW"
        return "WATCH"

    @staticmethod
    def get_channels(severity: str) -> List[str]:
        if severity == "CRITICAL":
            return ["DASHBOARD", "EMAIL", "TELEGRAM"]
        if severity == "URGENT":
            return ["DASHBOARD", "EMAIL"]
        return ["DASHBOARD"]

class OperatorEscalationService:
    """Manages the creation and lifecycle of operator escalations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.notifier = NotificationAdapter(db)

    async def create_escalation(
        self, 
        source_type: str, 
        source_id: uuid.UUID, 
        route: str, 
        failure_type: str,
        reason: str
    ) -> UIOperatorEscalation:
        # Check if active escalation already exists for this route/source
        stmt = select(UIOperatorEscalation).where(
            UIOperatorEscalation.route == route,
            UIOperatorEscalation.status.in_(["OPEN", "NOTIFIED", "ACKNOWLEDGED"])
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            return existing

        severity = EscalationPolicy.get_severity(failure_type, route, 1)
        channels = EscalationPolicy.get_channels(severity)

        escalation = UIOperatorEscalation(
            source_type=source_type,
            source_id=source_id,
            route=route,
            severity=severity,
            reason=reason,
            notification_channels_json=channels,
            status="OPEN"
        )
        self.db.add(escalation)
        await self.db.commit()
        await self.db.refresh(escalation)

        # Trigger notifications
        await self.notifier.send_escalation_notifications(escalation)
        
        return escalation

    async def acknowledge(self, escalation_id: uuid.UUID, operator_id: str):
        result = await self.db.execute(select(UIOperatorEscalation).filter_by(id=escalation_id))
        escalation = result.scalar_one_or_none()
        if escalation:
            escalation.status = "ACKNOWLEDGED"
            escalation.acknowledged_by = operator_id
            escalation.acknowledged_at = datetime.now(timezone.utc)
            await self.db.commit()

    async def resolve(self, escalation_id: uuid.UUID, operator_id: str):
        result = await self.db.execute(select(UIOperatorEscalation).filter_by(id=escalation_id))
        escalation = result.scalar_one_or_none()
        if escalation:
            escalation.status = "RESOLVED"
            escalation.resolved_by = operator_id
            escalation.resolved_at = datetime.now(timezone.utc)
            await self.db.commit()
