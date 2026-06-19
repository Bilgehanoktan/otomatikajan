import uuid
import hashlib
import json
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

class WarRoomEvidenceWriter:
    def __init__(self, db: Any):
        self.db = db

    def write_evidence(self, entity_id: uuid.UUID, action: str, data: Dict[str, Any], 
                       actor: str = "WarRoom_Engine") -> str:
        """
        Simulates writing evidence to the SovereignEvidence ledger.
        In a real system, this would call the EvidenceLedger service.
        Returns the evidence_hash.
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        raw_payload = {
            "entity_id": str(entity_id),
            "action": action,
            "data": data,
            "actor": actor,
            "timestamp": timestamp
        }
        
        payload_str = json.dumps(raw_payload, sort_keys=True)
        evidence_hash = hashlib.sha256(payload_str.encode()).hexdigest()
        
        # Log to system console/audit for now
        print(f"[EVIDENCE] {action} for {entity_id} - Hash: {evidence_hash}")
        
        return evidence_hash

    def write_execution_event(self, execution_id: uuid.UUID, event_type: str, detail: str):
        """Phase 27: Specific helper for Auto-Patch execution events."""
        return self.write_evidence(
            entity_id=execution_id,
            action=f"AUTOPATCH_{event_type.upper()}",
            data={"detail": detail},
            actor="AutoPatch_Orchestrator"
        )
