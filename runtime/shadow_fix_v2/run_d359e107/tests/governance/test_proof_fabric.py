import pytest
import uuid
from services.governance.proof_fabric import ProofFabric
from libs.db.session import get_sync_session
from libs.db.models.governance_models import ProofEventType, GovernorDomain, ProofSealStatus

def test_proof_fabric_integrity_chain(db_session):
    """
    Tests that ProofFabric correctly creates a chain of events with valid hashes.
    """
    fabric = ProofFabric(db_session)
    
    # 1. Record multiple events
    e1 = fabric.record_governance_event(
        event_type=ProofEventType.GOVERNOR_DECISION,
        domain=GovernorDomain.APPROVAL,
        entity_id=str(uuid.uuid4()),
        payload={"action": "APPROVE", "note": "Test 1"},
        actor="PYTEST_RUNNER"
    )
    
    e2 = fabric.record_governance_event(
        event_type=ProofEventType.CONFLICT_EVENT,
        domain=GovernorDomain.META,
        entity_id=str(uuid.uuid4()),
        payload={"conflict": "RISK_DISAGREEMENT"},
        actor="PYTEST_RUNNER"
    )
    
    # 2. Verify link
    assert e2.chain_index == e1.chain_index + 1
    assert e2.prev_event_hash == e1.event_hash
    
    # 3. Verify via chain service
    is_intact = fabric.chain_service.verify_chain_integrity(e1.chain_index, e2.chain_index)
    assert is_intact is True

def test_proof_fabric_snapshot_seal(db_session):
    """
    Tests the Merkle tree generation and snapshot sealing process.
    """
    fabric = ProofFabric(db_session)
    
    # 1. Ensure we have at least 1 event
    e1 = fabric.record_governance_event(
        event_type=ProofEventType.SNAPSHOT_SEAL,
        domain=GovernorDomain.META,
        entity_id=None,
        payload={"trigger": "manual_test"},
        actor="PYTEST_RUNNER"
    )
    
    # 2. Seal snapshot
    snapshot = fabric.seal_snapshot(
        snapshot_name=f"Pytest_Snap_{uuid.uuid4().hex[:8]}",
        start_idx=e1.chain_index,
        end_idx=e1.chain_index,
        actor="PYTEST_RUNNER"
    )
    
    assert snapshot.seal_status == ProofSealStatus.SEALED
    assert snapshot.merkle_root is not None
    assert snapshot.event_count >= 1
