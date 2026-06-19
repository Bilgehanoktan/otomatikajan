import pytest
import uuid
from services.governance.proof_fabric import ProofFabric
from services.governance.proof_verifier import ProofVerifier
from libs.db.session import get_sync_session
from libs.db.models.governance_models import GovernanceProofEventRecord, ProofEventType, GovernorDomain, ProofSealStatus

def test_verifier_detects_payload_tamper(db_session):
    """
    Simulation of a malicious database update and detection by the verifier.
    """
    fabric = ProofFabric(db_session)
    verifier = ProofVerifier(db_session)
    
    # 1. Create a valid event
    event = fabric.record_governance_event(
        event_type=ProofEventType.GOVERNOR_DECISION,
        domain=GovernorDomain.APPROVAL,
        entity_id=str(uuid.uuid4()),
        payload={"sensitive_data": "secret_123"},
        actor="SYSTEM"
    )
    
    # 2. Verify it's initially intact
    result_before = verifier.verify_event_chain(event.chain_index, event.chain_index)
    assert result_before["is_intact"] is True
    
    # 3. TAMPER: Manually modify the payload_canonical in the DB without updating hash
    db_session.execute(
        GovernanceProofEventRecord.__table__.update()
        .where(GovernanceProofEventRecord.id == event.id)
        .values(payload_canonical=event.payload_canonical.replace("secret_123", "HACKED"))
    )
    db_session.commit()
    db_session.expire_all() # Ensure we re-fetch from DB
    
    # 4. VERIFY: Should detect breakage
    result_after = verifier.verify_event_chain(event.chain_index, event.chain_index)
    assert result_after["is_intact"] is False
    assert result_after["status"] == ProofSealStatus.BROKEN

def test_verifier_detects_chain_break(db_session):
    """
    Simulation of breaking the link between two events.
    """
    fabric = ProofFabric(db_session)
    verifier = ProofVerifier(db_session)
    
    # 1. Create two events
    e1 = fabric.record_governance_event(ProofEventType.GOVERNOR_DECISION, GovernorDomain.APPROVAL, None, {"v": 1})
    e2 = fabric.record_governance_event(ProofEventType.GOVERNOR_DECISION, GovernorDomain.APPROVAL, None, {"v": 2})
    
    # 2. TAMPER: Modify prev_event_hash of e2
    db_session.execute(
        GovernanceProofEventRecord.__table__.update()
        .where(GovernanceProofEventRecord.id == e2.id)
        .values(prev_event_hash="invalid_hash_value")
    )
    db_session.commit()
    db_session.expire_all()
    
    # 3. VERIFY: Should detect chain breakage
    result = verifier.verify_event_chain(e1.chain_index, e2.chain_index)
    assert result["is_intact"] is False
