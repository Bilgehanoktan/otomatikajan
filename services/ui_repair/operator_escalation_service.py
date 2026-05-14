from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from sqlalchemy.orm import Session
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
    
    def __init__(self, db: Session):
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
        existing = self.db.query(UIOperatorEscalation).filter(
            UIOperatorEscalation.route == route,
            UIOperatorEscalation.status.in_(["OPEN", "NOTIFIED", "ACKNOWLEDGED"])
        ).first()
        
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
        self.db.commit()
        self.db.refresh(escalation)

        # Trigger notifications
        await self.notifier.send_escalation_notifications(escalation)
        
        return escalation

    async def acknowledge(self, escalation_id: uuid.UUID, operator_id: str):
        escalation = self.db.query(UIOperatorEscalation).filter_by(id=escalation_id).first()
        if escalation:
            escalation.status = "ACKNOWLEDGED"
            escalation.acknowledged_by = operator_id
            escalation.acknowledged_at = datetime.utcnow()
            self.db.commit()

    async def resolve(self, escalation_id: uuid.UUID, operator_id: str):
        escalation = self.db.query(UIOperatorEscalation).filter_by(id=escalation_id).first()
        if escalation:
            escalation.status = "RESOLVED"
            escalation.resolved_by = operator_id
            escalation.resolved_at = datetime.utcnow()
            self.db.commit()
