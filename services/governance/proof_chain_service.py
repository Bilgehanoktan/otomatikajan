import hashlib
import json
from typing import Any, Optional
from datetime import datetime
from libs.db.models.governance_models import GovernanceProofEventRecord, ProofEventType, GovernorDomain
from services.governance.proof_canonicalizer import canonicalize_payload
from libs.db.repositories.governance_proof_repository import GovernanceProofEventRepo
from sqlalchemy.orm import Session

class ProofChainService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = GovernanceProofEventRepo(db)

    def compute_payload_hash(self, canonical_payload: str) -> str:
        return hashlib.sha256(canonical_payload.encode('utf-8')).hexdigest()

    def get_last_chain_event(self) -> Optional[GovernanceProofEventRecord]:
        return self.repo.get_last_event()

    def append_event(self, 
                     event_type: ProofEventType, 
                     domain: Optional[GovernorDomain], 
                     entity_id: Optional[str], 
                     payload: Any, 
                     actor: Optional[str] = None) -> GovernanceProofEventRecord:
        """
        Calculates hashes and appends a new event to the immutable chain.
        """
        canonical = canonicalize_payload(payload)
        payload_hash = self.compute_payload_hash(canonical)
        
        last_event = self.get_last_chain_event()
        prev_hash = last_event.event_hash if last_event else "0" * 64
        chain_index = (last_event.chain_index + 1) if last_event else 0
        
        # event_hash = sha256(prev_event_hash + payload_hash + metadata)
        metadata_str = f"{event_type.value}:{domain.value if domain else 'NONE'}:{chain_index}"
        raw_to_hash = f"{prev_hash}{payload_hash}{metadata_str}"
        event_hash = hashlib.sha256(raw_to_hash.encode('utf-8')).hexdigest()
        
        event = GovernanceProofEventRecord(
            event_type=event_type,
            domain=domain,
            entity_id=entity_id,
            payload_hash=payload_hash,
            payload_canonical=canonical,
            prev_event_hash=prev_hash,
            event_hash=event_hash,
            chain_index=chain_index,
            created_by=actor
        )
        
        return self.repo.save_event(event)

    def verify_chain_integrity(self, start_index: int = 0, end_index: Optional[int] = None) -> bool:
        """
        Iterates through the chain and verifies each link.
        """
        events = self.repo.list_events(start_index, end_index)
        prev_hash = "0" * 64 if start_index == 0 else None
        
        for event in events:
            if prev_hash and event.prev_event_hash != prev_hash:
                return False
            
            # 1. Payload Content Check
            calc_payload_hash = self.compute_payload_hash(event.payload_canonical)
            if calc_payload_hash != event.payload_hash:
                return False

            # 2. Link Check
            metadata_str = f"{event.event_type.value}:{event.domain.value if event.domain else 'NONE'}:{event.chain_index}"
            raw_to_hash = f"{event.prev_event_hash}{event.payload_hash}{metadata_str}"
            calc_hash = hashlib.sha256(raw_to_hash.encode('utf-8')).hexdigest()
            
            if calc_hash != event.event_hash:
                return False
                
            prev_hash = event.event_hash
            
        return True
