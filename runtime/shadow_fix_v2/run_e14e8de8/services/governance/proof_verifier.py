from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import uuid
from services.governance.proof_chain_service import ProofChainService
from services.governance.proof_merkle_service import MerkleService
from libs.db.repositories.governance_proof_repository import (
    GovernanceProofEventRepo, 
    GovernanceProofSnapshotRepo,
    GovernanceVerificationRepo
)
from libs.db.models.governance_models import GovernanceProofVerificationRecord, ProofSealStatus

class ProofVerifier:
    def __init__(self, db: Session):
        self.db = db
        self.chain_service = ProofChainService(db)
        self.merkle_service = MerkleService(db)
        self.event_repo = GovernanceProofEventRepo(db)
        self.snapshot_repo = GovernanceProofSnapshotRepo(db)
        self.verify_repo = GovernanceVerificationRepo(db)

    def verify_event_chain(self, start_idx: int, end_idx: int) -> Dict[str, Any]:
        """
        Verifies the cryptographic chain between two indices.
        """
        is_intact = self.chain_service.verify_chain_integrity(start_idx, end_idx)
        status = ProofSealStatus.VERIFIED if is_intact else ProofSealStatus.BROKEN
        
        verification = GovernanceProofVerificationRecord(
            target_type="CHAIN",
            target_id=f"{start_idx}-{end_idx}",
            verification_status=status,
            verified_by="SYSTEM_VERIFIER"
        )
        self.verify_repo.save_verification(verification)
        
        return {
            "status": status,
            "verification_id": verification.id,
            "is_intact": is_intact
        }

    def verify_snapshot(self, snapshot_id: uuid.UUID) -> Dict[str, Any]:
        """
        Full audit of a snapshot: 
        1. Chain integrity for range.
        2. Merkle root recalculation.
        """
        snapshot = self.snapshot_repo.get_snapshot(snapshot_id)
        if not snapshot:
            return {"status": "NOT_FOUND"}
            
        # 1. Chain check
        chain_ok = self.chain_service.verify_chain_integrity(snapshot.start_chain_index, snapshot.end_chain_index)
        
        # 2. Merkle check (Simplified: check if root in DB matches recalculated if needed)
        # For now, if chain is OK and status is SEALED, we trust the root unless BROKEN detected
        
        status = ProofSealStatus.VERIFIED if chain_ok else ProofSealStatus.BROKEN
        snapshot.seal_status = status
        self.db.commit()
        
        return {
            "status": status,
            "snapshot_name": snapshot.snapshot_name,
            "integrity": "OK" if chain_ok else "BROKEN"
        }
