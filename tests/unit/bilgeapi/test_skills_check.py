import pytest
from unittest.mock import MagicMock
from apps.bilgeapi.services.skill_registry import SkillRegistryService
from apps.bilgeapi.services.skill_check_service import SkillCheckService
from apps.bilgeapi.schemas.skills import SkillMetadataResponse

class MockLedgerService:
    def __init__(self):
        self.events = []

    async def append_event(self, chain_id, event_type, entity_type, entity_id, actor_id, payload):
        self.events.append({
            "chain_id": chain_id,
            "event_type": event_type,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "actor_id": actor_id,
            "payload": payload
        })

@pytest.fixture
def mock_registry():
    registry = MagicMock(spec=SkillRegistryService)
    registry.initialized = True
    
    # Pre-populate metadata for the tests
    skills_db = {
        "bilgeapi-repair-request-safety": SkillMetadataResponse(
            name="bilgeapi-repair-request-safety", source="bilgeapi-custom", version="1.0.0",
            license="MIT", risk_level="high_value_policy", hash="h1", enabled=True
        ),
        "bilgeapi-pr-verification-gate": SkillMetadataResponse(
            name="bilgeapi-pr-verification-gate", source="bilgeapi-custom", version="1.0.0",
            license="MIT", risk_level="high_value_policy", hash="h2", enabled=True
        ),
        "bilgeapi-self-healing-policy": SkillMetadataResponse(
            name="bilgeapi-self-healing-policy", source="bilgeapi-custom", version="1.0.0",
            license="MIT", risk_level="high_value_policy", hash="h3", enabled=True
        ),
        "bilgeapi-skill-integrity": SkillMetadataResponse(
            name="bilgeapi-skill-integrity", source="bilgeapi-custom", version="1.0.0",
            license="MIT", risk_level="high_value_policy", hash="h4", enabled=True
        ),
        "security-and-hardening": SkillMetadataResponse(
            name="security-and-hardening", source="external-vendor", version="1.0.0",
            license="MIT", risk_level="low", hash="h5", enabled=True
        )
    }
    
    def get_skill_side_effect(name):
        if name in skills_db:
            return skills_db[name]
        raise ValueError(f"Skill {name} not found")
        
    registry.get_skill.side_effect = get_skill_side_effect
    return registry

@pytest.mark.asyncio
async def test_skill_check_happy_path(mock_registry):
    ledger = MockLedgerService()
    checker = SkillCheckService(registry=mock_registry, ledger_service=ledger)
    
    patch_code = "def add(a, b):\n    return a + b"
    response = await checker.check_patch(
        target_type="pr_draft",
        target_id="pr_123",
        skill_names=["bilgeapi-repair-request-safety"],
        patch_code=patch_code
    )
    
    assert response.passed is True
    assert response.status == "PASS"
    assert response.checks[0].result == "passed"
    
    # Verify ledger logged event
    assert len(ledger.events) == 1
    assert ledger.events[0]["event_type"] == "SKILL_CHECK_APPLIED"
    assert ledger.events[0]["payload"]["status"] == "PASS"

@pytest.mark.asyncio
async def test_skill_check_blocked_pattern(mock_registry):
    ledger = MockLedgerService()
    checker = SkillCheckService(registry=mock_registry, ledger_service=ledger)
    
    patch_code = "eval('dangerous_code')"
    response = await checker.check_patch(
        target_type="pr_draft",
        target_id="pr_123",
        skill_names=["bilgeapi-repair-request-safety"],
        patch_code=patch_code
    )
    
    assert response.passed is False
    assert response.status == "BLOCKED"
    assert response.checks[0].result == "blocked"
    assert "Forbidden patterns detected" in response.checks[0].reason
    
    assert len(ledger.events) == 1
    assert ledger.events[0]["event_type"] == "SKILL_CHECK_FAILED"
    assert ledger.events[0]["payload"]["status"] == "BLOCKED"

@pytest.mark.asyncio
async def test_skill_check_review_required(mock_registry):
    ledger = MockLedgerService()
    checker = SkillCheckService(registry=mock_registry, ledger_service=ledger)
    
    # Modifying database.py is review_required under bilgeapi-pr-verification-gate
    patch_code = "+++ b/apps/bilgeapi/database.py\n+new_db_helper()"
    response = await checker.check_patch(
        target_type="pr_draft",
        target_id="pr_123",
        skill_names=["bilgeapi-pr-verification-gate"],
        patch_code=patch_code
    )
    
    assert response.passed is False
    assert response.status == "REVIEW_REQUIRED"
    assert response.checks[0].result == "review_required"
    assert "Sensitive files modified" in response.checks[0].reason

@pytest.mark.asyncio
async def test_skill_integrity_violation(mock_registry):
    ledger = MockLedgerService()
    checker = SkillCheckService(registry=mock_registry, ledger_service=ledger)
    
    # Trying to modify SKILL_POLICY.md
    patch_code = "+++ b/docs/SKILL_POLICY.md\n-old_policy\n+new_policy"
    response = await checker.check_patch(
        target_type="pr_draft",
        target_id="pr_123",
        skill_names=["bilgeapi-skill-integrity"],
        patch_code=patch_code
    )
    
    assert response.passed is False
    assert response.status == "BLOCKED"
    assert response.checks[0].result == "blocked"
    assert "strictly forbidden" in response.checks[0].reason

@pytest.mark.asyncio
async def test_self_healing_policy_violation(mock_registry):
    ledger = MockLedgerService()
    checker = SkillCheckService(registry=mock_registry, ledger_service=ledger)
    
    # git push or subprocess inside self-healing
    patch_code = "git push origin main"
    response = await checker.check_patch(
        target_type="remediation",
        target_id="rem_456",
        skill_names=["bilgeapi-self-healing-policy"],
        patch_code=patch_code
    )
    
    assert response.passed is False
    assert response.status == "BLOCKED"
    assert response.checks[0].result == "blocked"
    assert "Forbidden git operations" in response.checks[0].reason

@pytest.mark.asyncio
async def test_unknown_skill_fails_closed(mock_registry):
    ledger = MockLedgerService()
    checker = SkillCheckService(registry=mock_registry, ledger_service=ledger)
    
    # Querying a skill that is not registered/allowlisted
    with pytest.raises(ValueError, match="Security violation: Unknown or un-allowlisted skill"):
        await checker.check_patch(
            target_type="pr_draft",
            target_id="pr_123",
            skill_names=["unknown-rogue-skill"],
            patch_code="print('hello')"
        )
        
    # Verify ledger was notified of blocked action
    assert len(ledger.events) == 1
    assert ledger.events[0]["event_type"] == "SKILL_POLICY_BLOCKED"
    assert "unknown-rogue-skill" in ledger.events[0]["payload"]["skill"]

@pytest.mark.asyncio
async def test_uninitialized_registry_fails_closed(mock_registry):
    mock_registry.initialized = False
    ledger = MockLedgerService()
    checker = SkillCheckService(registry=mock_registry, ledger_service=ledger)
    
    with pytest.raises(RuntimeError, match="has not been initialized"):
        await checker.check_patch(
            target_type="pr_draft",
            target_id="pr_123",
            skill_names=["bilgeapi-repair-request-safety"],
            patch_code="print('hello')"
        )
        
    assert len(ledger.events) == 1
    assert ledger.events[0]["event_type"] == "SKILL_POLICY_BLOCKED"
    assert "not initialized" in ledger.events[0]["payload"]["error"]
