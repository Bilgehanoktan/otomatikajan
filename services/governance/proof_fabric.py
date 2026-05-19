from typing import Any, Optional, List
import uuid
import hashlib
# from sqlalchemy.orm import Session
# from sqlalchemy.ext.asyncio import AsyncSession
# from libs.db.models.governance_models import (
#     ProofEventType, 
#     GovernorDomain, 
#     GovernanceProofSnapshotRecord,
#     ProofSealStatus
# )
# from services.governance.proof_chain_service import ProofChainService
# from services.governance.proof_merkle_service import MerkleService
# from libs.db.repositories.governance_proof_repository import (
#     GovernanceProofEventRepo,
#     GovernanceProofSnapshotRepo
# )

class ProofFabric:
    def __init__(self, db: Any):
        from services.governance.proof_chain_service import ProofChainService
        from libs.db.repositories.governance_proof_repository import (
            GovernanceProofEventRepo,
            GovernanceProofSnapshotRepo
        )
        self.db = db
        self.chain_service = ProofChainService(db)
        # Note: MerkleService and Repos might need async updates if used heavily,
        # but for now we focus on the record_governance_event path used by Lineage.
        self.event_repo = GovernanceProofEventRepo(db)
        self.snapshot_repo = GovernanceProofSnapshotRepo(db)

    def record_governance_event(self, 
                                event_type: Any, 
                                domain: Optional[Any], 
                                entity_id: Optional[str], 
                                payload: Any, 
                                actor: Optional[str] = None):
        from sqlalchemy.ext.asyncio import AsyncSession
        if isinstance(self.db, AsyncSession):
            raise RuntimeError("Use record_governance_event_async for AsyncSession")
        return self.chain_service.append_event(event_type, domain, entity_id, payload, actor)

    async def record_governance_event_async(self, 
                                            event_type: Any, 
                                            domain: Optional[Any], 
                                            entity_id: Optional[str], 
                                            payload: Any, 
                                            actor: Optional[str] = None):
        return await self.chain_service.append_event_async(event_type, domain, entity_id, payload, actor)

    def seal_snapshot(
        self,
        snapshot_name: str,
        start_idx: int,
        end_idx: int,
        actor: Optional[str] = None,
    ) -> Any:
        from libs.db.models.governance_models import GovernanceProofSnapshotRecord, ProofSealStatus
        from services.governance.proof_merkle_service import MerkleService

        events = self.event_repo.list_events(start_idx, end_idx)
        snapshot_id = uuid.uuid4()
        event_hashes = [event.event_hash for event in events]
        merkle_root = MerkleService(self.db).build_merkle_tree(snapshot_id, event_hashes)
        snapshot_hash = hashlib.sha256(
            f"{snapshot_name}:{start_idx}:{end_idx}:{merkle_root}".encode("utf-8")
        ).hexdigest()

        snapshot = GovernanceProofSnapshotRecord(
            id=snapshot_id,
            snapshot_name=snapshot_name,
            start_chain_index=start_idx,
            end_chain_index=end_idx,
            event_count=len(events),
            merkle_root=merkle_root,
            snapshot_hash=snapshot_hash,
            seal_status=ProofSealStatus.SEALED,
            sealed_by=actor,
        )
        return self.snapshot_repo.save_snapshot(snapshot)
