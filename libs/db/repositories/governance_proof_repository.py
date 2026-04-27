from sqlalchemy.orm import Session
from sqlalchemy import desc
from libs.db.models.governance_models import (
    GovernanceProofEventRecord, 
    GovernanceProofSnapshotRecord,
    GovernanceMerkleNodeRecord,
    GovernanceProofVerificationRecord
)
from typing import List, Optional
import uuid

class GovernanceProofEventRepo:
    def __init__(self, db: Session):
        self.db = db

    def save_event(self, event: GovernanceProofEventRecord) -> GovernanceProofEventRecord:
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def get_last_event(self) -> Optional[GovernanceProofEventRecord]:
        return self.db.query(GovernanceProofEventRecord).order_by(desc(GovernanceProofEventRecord.chain_index)).first()

    def list_events(self, start: int = 0, end: Optional[int] = None) -> List[GovernanceProofEventRecord]:
        query = self.db.query(GovernanceProofEventRecord).filter(GovernanceProofEventRecord.chain_index >= start)
        if end is not None:
            query = query.filter(GovernanceProofEventRecord.chain_index <= end)
        return query.order_by(GovernanceProofEventRecord.chain_index).all()


class GovernanceProofSnapshotRepo:
    def __init__(self, db: Session):
        self.db = db

    def save_snapshot(self, snapshot: GovernanceProofSnapshotRecord) -> GovernanceProofSnapshotRecord:
        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)
        return snapshot

    def get_snapshot(self, snapshot_id: uuid.UUID) -> Optional[GovernanceProofSnapshotRecord]:
        return self.db.query(GovernanceProofSnapshotRecord).filter(GovernanceProofSnapshotRecord.id == snapshot_id).first()

    def list_snapshots(self, limit: int = 50) -> List[GovernanceProofSnapshotRecord]:
        return self.db.query(GovernanceProofSnapshotRecord).order_by(desc(GovernanceProofSnapshotRecord.created_at)).limit(limit).all()


class GovernanceMerkleRepo:
    def __init__(self, db: Session):
        self.db = db

    def save_nodes(self, nodes: List[GovernanceMerkleNodeRecord]):
        self.db.add_all(nodes)
        self.db.commit()


class GovernanceVerificationRepo:
    def __init__(self, db: Session):
        self.db = db

    def save_verification(self, verification: GovernanceProofVerificationRecord) -> GovernanceProofVerificationRecord:
        self.db.add(verification)
        self.db.commit()
        self.db.refresh(verification)
        return verification
