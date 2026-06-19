import uuid
import hashlib
import json
from typing import Dict, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.core_models import SovereignEvidence

class DefenseEvidenceWriter:
    """Phase 25: Securely logs defense optimization events to the evidence ledger."""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def write_tuning_event(self, event_type: str, payload: Dict[str, Any], severity: str = "INFO"):
        """Writes a non-repudiable record of a tuning action."""
        
        content_json = json.dumps(payload, sort_keys=True)
        content_hash = hashlib.sha256(content_json.encode()).hexdigest()
        
        evidence = SovereignEvidence(
            id=uuid.uuid4(),
            evidence_type=f"DEFENSE_TUNING_{event_type}",
            severity=severity,
            payload=payload,
            provenance_hash=content_hash,
            created_at=datetime.now(timezone.utc)
        )
        
        self.db.add(evidence)
        await self.db.flush()
        return evidence
