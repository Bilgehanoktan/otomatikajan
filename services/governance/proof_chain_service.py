import hashlib
import json
from typing import Any, Optional
from datetime import datetime
# from libs.db.models.governance_models import GovernanceProofEventRecord, ProofEventType, GovernorDomain
from services.governance.proof_canonicalizer import canonicalize_payload
# from libs.db.repositories.governance_proof_repository import GovernanceProofEventRepo
# from sqlalchemy.orm import Session
# from sqlalchemy.ext.asyncio import AsyncSession

class ProofChainService:
    def __init__(self, db: Any):
        from libs.db.repositories.governance_proof_repository import GovernanceProofEventRepo
        self.db = db
        self.repo = GovernanceProofEventRepo(db)

    def compute_payload_hash(self, canonical_payload: str) -> str:
        return hashlib.sha256(canonical_payload.encode('utf-8')).hexdigest()

    def get_last_chain_event(self) -> Optional[Any]:
        return self.repo.get_last_event()

    async def get_last_chain_event_async(self) -> Optional[Any]:
        return await self.repo.get_last_event_async()

    def append_event(self, 
                     event_type: Any, 
                     domain: Optional[Any], 
                     entity_id: Optional[str], 
                     payload: Any, 
                     actor: Optional[str] = None) -> Any:
        """
        Calculates hashes and appends a new event to the immutable chain (Sync).
        """
        from libs.db.models.governance_models import GovernanceProofEventRecord
        canonical = canonicalize_payload(payload)
        payload_hash = self.compute_payload_hash(canonical)
        
        last_event = self.get_last_chain_event()
        prev_hash = last_event.event_hash if last_event else "0" * 64
        chain_index = (last_event.chain_index + 1) if last_event else 0
        
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

    async def append_event_async(self, 
                                 event_type: Any, 
                                 domain: Optional[Any], 
                                 entity_id: Optional[str], 
                                 payload: Any, 
                                 actor: Optional[str] = None) -> Any:
        """
        Calculates hashes and appends a new event to the immutable chain (Async).
        """
        from libs.db.models.governance_models import GovernanceProofEventRecord
        canonical = canonicalize_payload(payload)
        payload_hash = self.compute_payload_hash(canonical)
        
        last_event = await self.get_last_chain_event_async()
        prev_hash = last_event.event_hash if last_event else "0" * 64
        chain_index = (last_event.chain_index + 1) if last_event else 0
        
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
        
        return await self.repo.save_event_async(event)

    def verify_chain_integrity(self, start_idx: int = 0, end_idx: Optional[int] = None) -> bool:
        events = self.repo.list_events(0, end_idx)
        if not events:
            return True

        previous_hash = "0" * 64
        for event in events:
            expected_payload_hash = self.compute_payload_hash(event.payload_canonical)
            if event.payload_hash != expected_payload_hash:
                return False

            event_type = event.event_type.value if hasattr(event.event_type, "value") else str(event.event_type)
            domain = event.domain.value if hasattr(event.domain, "value") else (str(event.domain) if event.domain else "NONE")
            metadata_str = f"{event_type}:{domain}:{event.chain_index}"
            expected_event_hash = hashlib.sha256(
                f"{previous_hash}{event.payload_hash}{metadata_str}".encode("utf-8")
            ).hexdigest()

            if event.prev_event_hash != previous_hash or event.event_hash != expected_event_hash:
                return False

            previous_hash = event.event_hash
            if end_idx is not None and event.chain_index >= end_idx:
                break

        return True
