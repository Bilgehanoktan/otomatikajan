"""
Tests for Faz 10: Production Hardening measures.

H1: get_skill_registry returns 503 when registry unavailable
H2: Health endpoint reports skill_registry status (HEALTHY/DEGRADED)
H3: Exact canonical path matching in allowlist
H4: Manifest key set must exactly match allowlist
H5: Pattern detection uses regex (covered by existing tests)
"""
import os
import json
import pytest
from unittest.mock import MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
from bilgeapi.services.skill_registry import (
    SkillRegistryService,
    ALLOWED_SELECTED_SKILLS,
    ALLOWED_BILGEAPI_SKILLS,
)
from bilgeapi.schemas.skills import SkillMetadataResponse


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
            "payload": payload,
        })


# ─────────────────────────────────────────────────────────────────────────────
# H1: get_skill_registry returns 503 when registry is not available
# ─────────────────────────────────────────────────────────────────────────────

class TestH1RegistryDependency503:
    """When skill_registry is not set on app.state, catalog endpoints must return 503."""

    def test_catalog_skills_returns_503_without_registry(self):
        from bilgeapi.main import app
        from bilgeapi.routers.deps import get_skill_registry

        # Ensure no skill_registry on app.state
        if hasattr(app.state, "skill_registry"):
            delattr(app.state, "skill_registry")

        # Clear any overrides
        app.dependency_overrides.pop(get_skill_registry, None)

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/v1/catalog/skills")
        assert response.status_code == 503
        assert "not available" in response.json()["detail"].lower() or "degraded" in response.json()["detail"].lower()

    def test_catalog_skill_detail_returns_503_without_registry(self):
        from bilgeapi.main import app
        from bilgeapi.routers.deps import get_skill_registry

        if hasattr(app.state, "skill_registry"):
            delattr(app.state, "skill_registry")
        app.dependency_overrides.pop(get_skill_registry, None)

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/v1/catalog/skills/any-skill")
        assert response.status_code == 503


# ─────────────────────────────────────────────────────────────────────────────
# H2: Health endpoint reports skill_registry status
# ─────────────────────────────────────────────────────────────────────────────

class TestH2HealthSkillRegistryStatus:
    """Health endpoints should report skill_registry status."""

    def test_health_reports_healthy_when_registry_initialized(self):
        from bilgeapi.main import app
        app.state.skill_registry_status = "HEALTHY"

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/v1/ops/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["skill_registry"] == "HEALTHY"

    def test_health_reports_degraded_when_registry_failed(self):
        from bilgeapi.main import app
        app.state.skill_registry_status = "DEGRADED"

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/v1/ops/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["skill_registry"] == "DEGRADED"

    def test_health_reports_unknown_when_status_not_set(self):
        from bilgeapi.main import app
        if hasattr(app.state, "skill_registry_status"):
            delattr(app.state, "skill_registry_status")

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/v1/ops/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"  # UNKNOWN != HEALTHY → degraded
        assert data["skill_registry"] == "UNKNOWN"


# ─────────────────────────────────────────────────────────────────────────────
# H3: Exact canonical path matching prevents directory traversal
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def temp_skills_dir(tmp_path):
    """Create a valid skills directory structure with all allowlisted skills."""
    selected_dir = tmp_path / "docs" / "agent-skills" / "selected"
    bilgeapi_dir = tmp_path / "docs" / "agent-skills" / "bilgeapi"
    selected_dir.mkdir(parents=True, exist_ok=True)
    bilgeapi_dir.mkdir(parents=True, exist_ok=True)

    for s in ALLOWED_SELECTED_SKILLS:
        (selected_dir / f"{s}.md").write_text(f"---\nname: {s}\ndescription: Test\n---\nContent")
    for s in ALLOWED_BILGEAPI_SKILLS:
        (bilgeapi_dir / f"{s}.md").write_text(f"---\nname: {s}\ndescription: Test\n---\nContent")

    return tmp_path


class TestH3CanonicalPathMatching:
    """Exact canonical path matching blocks files in subdirectories."""

    @pytest.mark.asyncio
    async def test_rejects_md_file_in_subdirectory(self, temp_skills_dir):
        """A .md file in a nested subdirectory must be rejected."""
        subdir = temp_skills_dir / "docs" / "agent-skills" / "selected" / "nested"
        subdir.mkdir(parents=True, exist_ok=True)
        (subdir / "sneaky.md").write_text("---\nname: sneaky\n---\nMalicious")

        ledger = MockLedgerService()
        registry = SkillRegistryService(ledger_service=ledger, base_dir=str(temp_skills_dir))
        registry.generate_manifest()

        with pytest.raises(ValueError, match="unexpected subdirectory"):
            await registry.initialize_registry()

        assert registry.initialized is False

    @pytest.mark.asyncio
    async def test_rejects_symlink_outside_directory(self, temp_skills_dir):
        """A symlink pointing outside the allowed directory must be rejected."""
        # Create a file outside the skills dirs
        outside_file = temp_skills_dir / "secret.md"
        outside_file.write_text("SECRET DATA")

        # Create a symlink inside selected dir pointing to it
        link_path = temp_skills_dir / "docs" / "agent-skills" / "selected" / "symlink-attack.md"
        try:
            os.symlink(str(outside_file), str(link_path))
        except OSError:
            pytest.skip("Symlinks not supported on this platform/user")

        ledger = MockLedgerService()
        registry = SkillRegistryService(ledger_service=ledger, base_dir=str(temp_skills_dir))
        registry.generate_manifest()

        with pytest.raises(ValueError, match="Un-allowlisted skill file detected"):
            await registry.initialize_registry()

    @pytest.mark.asyncio
    async def test_canonical_happy_path(self, temp_skills_dir):
        """Valid allowlisted files in correct directory pass initialization."""
        ledger = MockLedgerService()
        registry = SkillRegistryService(ledger_service=ledger, base_dir=str(temp_skills_dir))
        registry.generate_manifest()
        await registry.initialize_registry()
        assert registry.initialized is True


# ─────────────────────────────────────────────────────────────────────────────
# H4: Manifest key set must exactly match allowlist
# ─────────────────────────────────────────────────────────────────────────────

class TestH4ManifestKeySetMatching:
    """hash_manifest.json must have exactly the expected key set."""

    @pytest.mark.asyncio
    async def test_extra_manifest_key_rejected(self, temp_skills_dir):
        """Extra keys in manifest (not in allowlist) must be rejected."""
        ledger = MockLedgerService()
        registry = SkillRegistryService(ledger_service=ledger, base_dir=str(temp_skills_dir))
        manifest = registry.generate_manifest()

        # Inject an extra key into the manifest
        manifest["rogue/injected-skill"] = "fakehash123"
        with open(registry.manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f)

        with pytest.raises(ValueError, match="un-allowlisted keys"):
            await registry.initialize_registry()

        assert registry.initialized is False

    @pytest.mark.asyncio
    async def test_missing_manifest_key_rejected(self, temp_skills_dir):
        """Missing expected keys in manifest must be rejected."""
        ledger = MockLedgerService()
        registry = SkillRegistryService(ledger_service=ledger, base_dir=str(temp_skills_dir))
        manifest = registry.generate_manifest()

        # Remove a required key
        first_key = list(manifest.keys())[0]
        del manifest[first_key]
        with open(registry.manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f)

        with pytest.raises(ValueError, match="missing required keys"):
            await registry.initialize_registry()

        assert registry.initialized is False

    @pytest.mark.asyncio
    async def test_exact_key_set_passes(self, temp_skills_dir):
        """Exactly matching key set passes validation."""
        ledger = MockLedgerService()
        registry = SkillRegistryService(ledger_service=ledger, base_dir=str(temp_skills_dir))
        registry.generate_manifest()
        await registry.initialize_registry()
        assert registry.initialized is True

        # Verify the expected number of keys
        expected_count = len(ALLOWED_SELECTED_SKILLS) + len(ALLOWED_BILGEAPI_SKILLS)
        assert len(registry.hash_manifest) == expected_count
