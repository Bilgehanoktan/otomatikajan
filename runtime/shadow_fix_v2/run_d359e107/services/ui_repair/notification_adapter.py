import asyncio
from typing import List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.ui_repair_models import UIOperatorEscalation, UINotificationDelivery

class NotificationAdapter:
    """Handles delivery of notifications via various channels."""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def send_escalation_notifications(self, escalation: UIOperatorEscalation):
        channels = escalation.notification_channels_json
        tasks = []
        for channel in channels:
            tasks.append(self.dispatch(escalation, channel))
        
        results = await asyncio.gather(*tasks)
        
        # Update escalation status
        statuses = {res['channel']: res['status'] for res in results}
        escalation.notification_status_json = statuses
        if any(r['status'] == 'SENT' for r in results):
            escalation.status = "NOTIFIED"
        else:
            escalation.status = "FAILED_TO_NOTIFY"
        
        await self.db.commit()

    async def dispatch(self, escalation: UIOperatorEscalation, channel: str) -> Dict[str, Any]:
        delivery = UINotificationDelivery(
            escalation_id=escalation.id,
            channel=channel,
            status="PENDING",
            recipient=self._get_recipient(channel),
            title=f"UI Failure Escalation: {escalation.severity}",
            message_summary=escalation.reason[:200]
        )
        self.db.add(delivery)
        await self.db.commit()

        try:
            # Mock delivery logic
            await asyncio.sleep(0.5) 
            
            # In real system, call Telegram/Email API here
            success = True 
            
            if success:
                delivery.status = "SENT"
                delivery.sent_at = datetime.now(timezone.utc)
            else:
                delivery.status = "FAILED"
                delivery.failed_at = datetime.now(timezone.utc)
                delivery.error_message = "Provider rejected request"
                
        except Exception as e:
            delivery.status = "FAILED"
            delivery.failed_at = datetime.now(timezone.utc)
            delivery.error_message = str(e)
        
        await self.db.commit()
        return {"channel": channel, "status": delivery.status}

    def _get_recipient(self, channel: str) -> str:
        if channel == "EMAIL": return "admin@sovereign-agi.local"
        if channel == "TELEGRAM": return "@SovereignOpsBot"
        return "SYSTEM"

    async def send_alert(self, message: str):
        """Sends an urgent alert/notification."""
        from services.observability.logging import get_logger
        logger = get_logger("notification_adapter")
        logger.warning(f"[ALERT] {message}")

