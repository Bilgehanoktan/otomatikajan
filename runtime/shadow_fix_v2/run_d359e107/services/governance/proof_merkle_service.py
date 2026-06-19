import hashlib
from typing import List, Optional, Dict
from libs.db.models.governance_models import GovernanceMerkleNodeRecord, GovernanceProofSnapshotRecord
from sqlalchemy.orm import Session
import uuid

class MerkleService:
    def __init__(self, db: Session):
        self.db = db

    def compute_hash(self, left: str, right: str) -> str:
        return hashlib.sha256(f"{left}{right}".encode('utf-8')).hexdigest()

    def build_merkle_tree(self, snapshot_id: uuid.UUID, leaves: List[str]) -> str:
        """
        Builds a Merkle tree from event hashes and saves nodes to DB.
        Returns the Merkle root.
        """
        if not leaves:
            return "0" * 64

        current_level = leaves
        level_idx = 0
        
        # Save leaves as Level 0
        for i, h in enumerate(current_level):
            self.db.add(GovernanceMerkleNodeRecord(
                snapshot_id=snapshot_id,
                node_level=level_idx,
                node_index=i,
                node_hash=h
            ))

        while len(current_level) > 1:
            level_idx += 1
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i+1] if i+1 < len(current_level) else left # Duplicate if odd
                
                combined_hash = self.compute_hash(left, right)
                next_level.append(combined_hash)
                
                self.db.add(GovernanceMerkleNodeRecord(
                    snapshot_id=snapshot_id,
                    node_level=level_idx,
                    node_index=len(next_level) - 1,
                    left_hash=left,
                    right_hash=right,
                    node_hash=combined_hash
                ))
            current_level = next_level

        self.db.commit()
        return current_level[0]

    def generate_proof(self, snapshot_id: uuid.UUID, event_index: int) -> List[Dict]:
        """
        Generates a Merkle proof path for an event at a given index within a snapshot.
        """
        # This would involve querying the saved nodes level by level
        # Simplified implementation for now
        return []

    def verify_proof(self, root: str, leaf: str, proof_path: List[Dict]) -> bool:
        current = leaf
        for p in proof_path:
            if p['side'] == 'left':
                current = self.compute_hash(p['hash'], current)
            else:
                current = self.compute_hash(current, p['hash'])
        return current == root
