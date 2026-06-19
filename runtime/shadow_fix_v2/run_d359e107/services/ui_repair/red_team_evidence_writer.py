import uuid
import json
import hashlib
from typing import Dict, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.core_models import SovereignEvidence

class RedTeamEvidenceWriter:
    """Phase 24: Securely logs Red Team events to the SovereignEvidence ledger."""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def write_event(self, event_type: str, payload: Dict[str, Any], severity: str = "INFO"):
        """Writes a non-repudiable record to the evidence chain."""
        
        content_json = json.dumps(payload, sort_keys=True)
        content_hash = hashlib.sha256(content_json.encode()).hexdigest()
        
        evidence = SovereignEvidence(
            id=uuid.uuid4(),
            evidence_type=f"RED_TEAM_{event_type}",
            severity=severity,
            payload=payload,
            provenance_hash=content_hash,
            created_at=datetime.now(timezone.utc)
        )
        
        self.db.add(evidence)
        await self.db.flush()
        return evidence
