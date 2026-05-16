import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.ui_repair_models import UISovereignIdentity, IdentityType, IdentityStatus
from services.ui_repair.sovereign_identity_registry import SovereignIdentityRegistry
from services.ui_repair.capability_token_service import CapabilityTokenService
from services.ui_repair.zero_trust_handshake import ZeroTrustHandshake
from services.ui_repair.trust_score_engine import TrustScoreEngine
from services.ui_repair.identity_policy_enforcer import IdentityPolicyEnforcer

@pytest.mark.asyncio
async def test_identity_registration(db_session: AsyncSession):
    registry = SovereignIdentityRegistry(db_session)
    data = {
        "identity_key": "test_agent_01",
        "identity_type": IdentityType.AGENT,
        "display_name": "Test Agent 01",
        "tenant_key": "TENANT_A",
        "fingerprint": "abc-123-xyz"
    }
    identity = await registry.register_identity(data)
    assert identity.identity_key == "test_agent_01"
    assert identity.status == IdentityStatus.ACTIVE
    
    # Check trust score initialization
    engine = TrustScoreEngine(db_session)
    score = await engine.get_score("test_agent_01")
    assert score == 1.0

@pytest.mark.asyncio
async def test_capability_token_lifecycle(db_session: AsyncSession):
    service = CapabilityTokenService(db_session)
    token = await service.issue_token(
        identity_key="test_agent_01",
        scope={"tenant_key": "TENANT_A"},
        actions=["READ_EVIDENCE", "POST_PR"]
    )
    assert token.token_id is not None
    
    # Validate valid token
    valid, reason = await service.validate_token(
        token.token_id, "READ_EVIDENCE", {"tenant_key": "TENANT_A"}
    )
    assert valid is True
    
    # Validate invalid action
    valid, reason = await service.validate_token(
        token.token_id, "DELETE_REPO", {"tenant_key": "TENANT_A"}
    )
    assert valid is False
    assert "not permitted" in reason

@pytest.mark.asyncio
async def test_zero_trust_handshake(db_session: AsyncSession):
    registry = SovereignIdentityRegistry(db_session)
    await registry.seed_identities()
    
    handshake_svc = ZeroTrustHandshake(db_session)
    req = {
        "source_identity_key": "stagehand_agent",
        "target_identity_key": "openswe_agent",
        "nonce": str(uuid.uuid4()),
        "action_type": "TRIGGER_REPAIR",
        "tenant_key": "GLOBAL",
        "project_key": "GLOBAL",
        "cluster_key": "GLOBAL",
        "signature": "mock_sig"
    }
    
    success, status, handshake = await handshake_svc.verify_handshake(req)
    assert success is True
    assert status == "PASSED"
    assert handshake.source_identity_key == "stagehand_agent"

@pytest.mark.asyncio
async def test_trust_score_decay(db_session: AsyncSession):
    engine = TrustScoreEngine(db_session)
    # Seed identity first
    registry = SovereignIdentityRegistry(db_session)
    await registry.register_identity({"identity_key": "bad_actor", "identity_type": IdentityType.WORKER, "display_name": "Bad Actor"})
    
    # Record violations
    await engine.record_event("bad_actor", "POLICY_VIOLATION", success=False)
    await engine.record_event("bad_actor", "POLICY_VIOLATION", success=False)
    
    score = await engine.get_score("bad_actor")
    assert score == pytest.approx(0.6) # 1.0 - 0.2 - 0.2

@pytest.mark.asyncio
async def test_identity_policy_enforcement(db_session: AsyncSession):
    enforcer = IdentityPolicyEnforcer(db_session)
    registry = SovereignIdentityRegistry(db_session)
    
    # Register agent with specific actions
    await registry.register_identity({
        "identity_key": "restricted_agent",
        "identity_type": IdentityType.AGENT,
        "display_name": "Restricted Agent",
        "allowed_actions": ["VIEW_HEALTH"]
    })
    
    # Test allowed action
    allowed, reason = await enforcer.authorize_action("restricted_agent", "VIEW_HEALTH", {"tenant_key": "GLOBAL"})
    assert allowed is True
    
    # Test unauthorized action
    allowed, reason = await enforcer.authorize_action("restricted_agent", "APPLY_PATCH", {"tenant_key": "GLOBAL"})
    assert allowed is False
    assert "ACTION_NOT_PERMITTED" in reason
