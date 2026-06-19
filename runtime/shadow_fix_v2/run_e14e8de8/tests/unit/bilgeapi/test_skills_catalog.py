import os
import json
import pytest
from unittest.mock import MagicMock, patch
from apps.bilgeapi.services.skill_registry import SkillRegistryService, ALLOWED_SELECTED_SKILLS, ALLOWED_BILGEAPI_SKILLS

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
def temp_skills_dir(tmp_path):
    # Setup folders
    selected_dir = tmp_path / "docs" / "agent-skills" / "selected"
    bilgeapi_dir = tmp_path / "docs" / "agent-skills" / "bilgeapi"
    selected_dir.mkdir(parents=True, exist_ok=True)
    bilgeapi_dir.mkdir(parents=True, exist_ok=True)
    
    # Write a few valid allowlisted skill files
    valid_selected = ALLOWED_SELECTED_SKILLS[0]
    valid_bilgeapi = ALLOWED_BILGEAPI_SKILLS[0]
    
    selected_file = selected_dir / f"{valid_selected}.md"
    selected_file.write_text(f"---\nname: {valid_selected}\ndescription: Test Selected\n---\nBody content selected")
    
    bilgeapi_file = bilgeapi_dir / f"{valid_bilgeapi}.md"
    bilgeapi_file.write_text(f"---\nname: {valid_bilgeapi}\ndescription: Test Bilgeapi\n---\nBody content bilgeapi")
    
    # Write all other allowlisted skills as empty dummy files to pass directory scans
    for s in ALLOWED_SELECTED_SKILLS[1:]:
        (selected_dir / f"{s}.md").write_text(f"---\nname: {s}\ndescription: Empty general\n---\nContent")
    for s in ALLOWED_BILGEAPI_SKILLS[1:]:
        (bilgeapi_dir / f"{s}.md").write_text(f"---\nname: {s}\ndescription: Empty custom\n---\nContent")
        
    return tmp_path

@pytest.mark.asyncio
async def test_registry_happy_path(temp_skills_dir):
    ledger = MockLedgerService()
    registry = SkillRegistryService(ledger_service=ledger, base_dir=str(temp_skills_dir))
    
    # Generate manifest (build step)
    manifest = registry.generate_manifest()
    assert len(manifest) == len(ALLOWED_SELECTED_SKILLS) + len(ALLOWED_BILGEAPI_SKILLS)
    assert os.path.exists(registry.manifest_path)
    
    # Initialize registry (startup step)
    await registry.initialize_registry()
    assert registry.initialized is True
    
    # List and get from cache
    skills = registry.list_skills()
    assert len(skills) == len(ALLOWED_SELECTED_SKILLS) + len(ALLOWED_BILGEAPI_SKILLS)
    
    # Verify no disk read on retrieval (mock open and verify it's not called during get_skill)
    skill_name = ALLOWED_SELECTED_SKILLS[0]
    with patch("builtins.open") as mock_open:
        skill = registry.get_skill(skill_name)
        assert skill.name == skill_name
        mock_open.assert_not_called()

    # Check that ledger events are recorded
    event_types = [e["event_type"] for e in ledger.events]
    assert "SKILL_CATALOG_LOADED" in event_types
    assert "SKILL_HASH_VERIFIED" in event_types

def test_path_traversal_prevention(temp_skills_dir):
    registry = SkillRegistryService(base_dir=str(temp_skills_dir))
    
    # Valid path inside directory
    inside_path = os.path.join(registry.selected_dir, "test.md")
    assert registry.validate_safe_path(registry.selected_dir, inside_path) == os.path.realpath(inside_path)
    
    # Invalid path outside base directory (path traversal)
    outside_path = os.path.join(registry.selected_dir, "..", "..", "secrets.json")
    with pytest.raises(ValueError, match="path traversal detected"):
        registry.validate_safe_path(registry.selected_dir, outside_path)

@pytest.mark.asyncio
async def test_allowlist_enforcement_rejects_unapproved_file(temp_skills_dir):
    # Add an un-allowlisted file to docs/agent-skills/selected
    unapproved_file = temp_skills_dir / "docs" / "agent-skills" / "selected" / "unapproved-skill.md"
    unapproved_file.write_text("---name: unapproved\n---")
    
    ledger = MockLedgerService()
    registry = SkillRegistryService(ledger_service=ledger, base_dir=str(temp_skills_dir))
    registry.generate_manifest()
    
    # Running initialize_registry should fail-closed
    with pytest.raises(ValueError, match="Un-allowlisted skill file detected"):
        await registry.initialize_registry()
        
    assert registry.initialized is False
    assert len(registry.verified_cache) == 0
    
    # Ledger should contain a blocked event
    event_types = [e["event_type"] for e in ledger.events]
    assert "SKILL_POLICY_BLOCKED" in event_types

@pytest.mark.asyncio
async def test_hash_mismatch_fails_closed(temp_skills_dir):
    ledger = MockLedgerService()
    registry = SkillRegistryService(ledger_service=ledger, base_dir=str(temp_skills_dir))
    registry.generate_manifest()
    
    # Tamper with a skill file after manifest has been generated
    tampered_file = temp_skills_dir / "docs" / "agent-skills" / "selected" / f"{ALLOWED_SELECTED_SKILLS[0]}.md"
    tampered_file.write_text("tampered content changes hash")
    
    # Running initialize_registry must fail-closed due to hash mismatch
    with pytest.raises(ValueError, match="Hash mismatch"):
        await registry.initialize_registry()
        
    assert registry.initialized is False
    assert len(registry.verified_cache) == 0
    
    event_types = [e["event_type"] for e in ledger.events]
    assert "SKILL_CHECK_FAILED" in event_types
    assert "SKILL_POLICY_BLOCKED" in event_types

@pytest.mark.asyncio
async def test_registry_uninitialized_throws_on_retrieve(temp_skills_dir):
    registry = SkillRegistryService(base_dir=str(temp_skills_dir))
    
    with pytest.raises(RuntimeError, match="has not been initialized"):
        registry.list_skills()
        
    with pytest.raises(RuntimeError, match="has not been initialized"):
        registry.get_skill("any-skill")
