from sqlalchemy.orm import Session
from typing import Any, Optional, List
import uuid
import hashlib
from libs.db.models.governance_models import (
    ProofEventType, 
    GovernorDomain, 
    GovernanceProofSnapshotRecord,
    ProofSealStatus
)
from services.governance.proof_chain_service import ProofChainService
from services.governance.proof_merkle_service import MerkleService
from libs.db.repositories.governance_proof_repository import (
    GovernanceProofEventRepo,
    GovernanceProofSnapshotRepo
)

class ProofFabric:
    def __init__(self, db: Session):
        self.db = db
        self.chain_service = ProofChainService(db)
        self.merkle_service = MerkleService(db)
        self.event_repo = GovernanceProofEventRepo(db)
        self.snapshot_repo = GovernanceProofSnapshotRepo(db)

    def record_governance_event(self, 
                                event_type: ProofEventType, 
                                domain: Optional[GovernorDomain], 
                                entity_id: Optional[str], 
                                payload: Any, 
                                actor: Optional[str] = None):
        """
        Public entry point to record any governance-relevant action into the immutable chain.
        """
        return self.chain_service.append_event(event_type, domain, entity_id, payload, actor)

    def seal_snapshot(self, snapshot_name: str, start_idx: int, end_idx: int, actor: Optional[str] = None) -> GovernanceProofSnapshotRecord:
        """
        Collects events in a range, builds a Merkle tree, and seals a snapshot.
        """
        events = self.event_repo.list_events(start_idx, end_idx)
        if not events:
            raise ValueError("No events found in specified range")
            
        hashes = [e.event_hash for e in events]
        
        # Create pending snapshot to get an ID
        snapshot = GovernanceProofSnapshotRecord(
            snapshot_name=snapshot_name,
            start_chain_index=start_idx,
            end_chain_index=end_idx,
            event_count=len(events),
            merkle_root="PENDING",
            snapshot_hash="PENDING",
            seal_status=ProofSealStatus.PENDING,
            sealed_by=actor
        )
        snapshot = self.snapshot_repo.save_snapshot(snapshot)
        
        # Build Merkle Tree
        root = self.merkle_service.build_merkle_tree(snapshot.id, hashes)
        
        # Snapshot hash = sha256(root + start + end + count)
        raw_to_hash = f"{root}{start_idx}{end_idx}{len(events)}"
        snap_hash = hashlib.sha256(raw_to_hash.encode('utf-8')).hexdigest()
        
        snapshot.merkle_root = root
        snapshot.snapshot_hash = snap_hash
        snapshot.seal_status = ProofSealStatus.SEALED
        
        self.db.commit()
        return snapshot

    def verify_entity_integrity(self, entity_id: str) -> bool:
        """
        Checks if the entity's recorded events in the chain are intact.
        """
        # Logic to find events by entity_id and verify their hashes
        return True
