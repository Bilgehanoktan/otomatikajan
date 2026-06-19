import json
import os
from typing import Optional
from sqlalchemy.orm import Session
from libs.db.repositories.governance_proof_repository import (
    GovernanceProofEventRepo, 
    GovernanceProofSnapshotRepo
)

class AuditBundleExporter:
    def __init__(self, db: Session):
        self.db = db
        self.event_repo = GovernanceProofEventRepo(db)
        self.snapshot_repo = GovernanceProofSnapshotRepo(db)

    def export_bundle(self, snapshot_id: str, target_dir: str) -> str:
        """
        Generates a portable audit bundle (JSON manifest + events).
        """
        snapshot = self.snapshot_repo.get_snapshot(snapshot_id)
        if not snapshot:
            raise ValueError("Snapshot not found")
            
        events = self.event_repo.list_events(snapshot.start_chain_index, snapshot.end_chain_index)
        
        bundle = {
            "manifest": {
                "snapshot_id": str(snapshot.id),
                "snapshot_name": snapshot.snapshot_name,
                "merkle_root": snapshot.merkle_root,
                "snapshot_hash": snapshot.snapshot_hash,
                "event_count": snapshot.event_count,
                "chain_range": [snapshot.start_chain_index, snapshot.end_chain_index],
                "sealed_at": snapshot.created_at.isoformat()
            },
            "events": [
                {
                    "type": e.event_type.value,
                    "index": e.chain_index,
                    "payload_hash": e.payload_hash,
                    "event_hash": e.event_hash,
                    "prev_hash": e.prev_event_hash,
                    "canonical": e.payload_canonical,
                    "created_at": e.created_at.isoformat()
                } for e in events
            ]
        }
        
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
            
        filename = f"audit_bundle_{snapshot.id}.json"
        filepath = os.path.join(target_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(bundle, f, indent=2, ensure_ascii=False)
            
        return filepath
