import logging
import uuid
import json
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.ui_repair_models import UISecurityRemediationEvent

logger = logging.getLogger(__name__)

class RemediationEvidenceWriter:
    """Phase 22: Records remediation steps into the non-repudiable evidence chain."""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_event(
        self, 
        finding_id: uuid.UUID,
        plan_id: uuid.UUID,
        event_type: str,
        message: str,
        payload: Dict[str, Any],
        attempt_id: Optional[uuid.UUID] = None
    ) -> UISecurityRemediationEvent:
        """Logs a remediation event with an evidence hash."""
        
        # Generate evidence hash
        canonical_data = {
            "finding_id": str(finding_id),
            "plan_id": str(plan_id),
            "event_type": event_type,
            "payload": payload,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        evidence_hash = hashlib.sha256(json.dumps(canonical_data, sort_keys=True).encode()).hexdigest()
        
        event = UISecurityRemediationEvent(
            id=uuid.uuid4(),
            finding_id=finding_id,
            plan_id=plan_id,
            attempt_id=attempt_id,
            event_type=event_type,
            message=message,
            payload_json=payload,
            evidence_hash=evidence_hash
        )
        
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        
        return event
