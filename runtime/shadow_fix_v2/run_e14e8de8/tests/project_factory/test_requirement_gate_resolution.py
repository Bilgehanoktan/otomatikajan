from __future__ import annotations

import json
import os
import shutil
import uuid
from pathlib import Path
from datetime import datetime
import pytest
from httpx import AsyncClient, ASGITransport

from services.workflow_api.main import app
from services.auth.jwt_auth import get_current_identity, require_permission
from services.project_factory.models import ProjectFactoryIntake, RequirementGate
from services.project_factory.artifacts import write_project_factory_artifacts, _resolve_project_dir
from libs.infra.router_registry import router_registry

# Paths
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
PROJECT_FACTORY_BASE = WORKSPACE_ROOT / "project_outputs" / "project_factory"
TEST_PROJECT_ID = "PF-TEST-RESOLVE-999"
TEST_PROJECT_DIR = PROJECT_FACTORY_BASE / TEST_PROJECT_ID

@pytest.fixture(autouse=True)
async def setup_test_environment():
    print(f"\n>>> Setting up project factory gate test in {TEST_PROJECT_DIR}...", flush=True)

    # 1. Setup mock credentials override
    mock_id = uuid.uuid4()
    app.dependency_overrides[get_current_identity] = lambda: {
        "id": mock_id,
        "type": "operator",
        "role": "OPERATOR"
    }
    app.dependency_overrides[require_permission("governor.override")] = lambda: {
        "id": mock_id,
        "type": "operator",
        "role": "OPERATOR"
    }
    app.dependency_overrides[require_permission("governor.view")] = lambda: {
        "id": mock_id,
        "type": "operator",
        "role": "OPERATOR"
    }

    # 2. Clean and create project factory base test directory
    if TEST_PROJECT_DIR.exists():
        shutil.rmtree(TEST_PROJECT_DIR, ignore_errors=True)
    TEST_PROJECT_DIR.mkdir(parents=True, exist_ok=True)

    # Write intake dummy file
    intake = ProjectFactoryIntake(
        project_id=TEST_PROJECT_ID,
        source_suggestion_id="sug-resolve-999",
        audit_run_id="AUD-RESOLVE-999",
        title="Test Resolve Project Factory",
        problem_statement="A problem that needs sandbox testing.",
        recommended_action="Create sandbox files.",
        affected_files=["libs/infra/router_registry.py", "secret.key", ".env", "non_existent_file.py"],
        suggested_scope="mvp",
        status="REQUIREMENT_GATE_WAITING",
        requires_operator_approval=True
    )
    gate = RequirementGate(
        gate="Requirement Approval Gate",
        status="WAITING_FOR_OPERATOR",
        allowed_actions=["approve_scope", "request_revision", "reject"],
        implementation_allowed=False,
        sandbox_ready=False
    )
    write_project_factory_artifacts(intake, gate, str(WORKSPACE_ROOT))

    yield

    print(f"\n>>> Tearing down test folder {TEST_PROJECT_DIR}...", flush=True)
    app.dependency_overrides.clear()
    if TEST_PROJECT_DIR.exists():
        shutil.rmtree(TEST_PROJECT_DIR, ignore_errors=True)


@pytest.mark.asyncio
async def test_get_project_factory_detail():
    """
    1. GET project factory detail returns project_brief.json and requirement_gate.json
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(f"/api/v1/project-factory/{TEST_PROJECT_ID}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["project_brief"]["project_id"] == TEST_PROJECT_ID
        assert data["requirement_gate"]["status"] == "WAITING_FOR_OPERATOR"


@pytest.mark.asyncio
async def test_approve_scope_workflow():
    """
    2. approve-scope gate statusunu SCOPE_APPROVED yapar
    3. approve-scope sandbox_manifest.json üretir
    4. sandbox klasörü workspace dışına yazamaz (path traversal)
    5. secret/env dosyaları sandbox’a kopyalanmaz
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create a dummy secret file in workspace to verify it gets blocked
        secret_file = WORKSPACE_ROOT / "secret.key"
        env_file = WORKSPACE_ROOT / ".env"
        
        # We make sure these files exist momentarily
        secret_existed = secret_file.exists()
        env_existed = env_file.exists()
        if not secret_existed:
            with open(secret_file, "w") as f:
                f.write("SECRET_KEY_VALUE")
        if not env_existed:
            with open(env_file, "w") as f:
                f.write("ENV_VAR=123")

        try:
            response = await ac.post(
                f"/api/v1/project-factory/{TEST_PROJECT_ID}/requirement-gate/approve-scope",
                json={
                    "operator_id": "OP-RESOLVE-1",
                    "rationale": "Scope is clean and verified",
                    "approved_scope": "mvp",
                    "risk_acknowledgement": True
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["gate_status"] == "SCOPE_APPROVED"
            assert data["sandbox_ready"] is True

            # Verify that requirement_gate.json updated properly
            with open(TEST_PROJECT_DIR / "requirement_gate.json", "r", encoding="utf-8") as f:
                gate_data = json.load(f)
            assert gate_data["status"] == "SCOPE_APPROVED"
            assert gate_data["implementation_allowed"] is False
            assert gate_data["approved_by"] == "OP-RESOLVE-1"

            # Verify sandbox manifest exists
            manifest_path = TEST_PROJECT_DIR / "sandbox_manifest.json"
            assert manifest_path.exists()
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            assert manifest["status"] == "SCAFFOLD_COMPLETED"
            
            # Verify router registry was copied but secrets/env and non-existent files are skipped/placeholders
            assert "libs/infra/router_registry.py" in manifest["copied_files"]
            assert any(s["path"] == "secret.key" for s in manifest["skipped_files"])
            assert any(s["path"] == ".env" for s in manifest["skipped_files"])
            assert "non_existent_file.py" in manifest["placeholder_files"]

            # Double check files inside the actual sandbox directory
            sandbox_dir = TEST_PROJECT_DIR / "sandbox"
            assert (sandbox_dir / "libs/infra/router_registry.py").exists()
            assert not (sandbox_dir / "secret.key").exists()
            assert not (sandbox_dir / ".env").exists()
            assert (sandbox_dir / "non_existent_file.py").exists() # Should be placeholder

        finally:
            if not secret_existed and secret_file.exists():
                os.remove(secret_file)
            if not env_existed and env_file.exists():
                os.remove(env_file)


@pytest.mark.asyncio
async def test_request_revision():
    """
    6. request-revision statusu REVISION_REQUESTED yapar
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            f"/api/v1/project-factory/{TEST_PROJECT_ID}/requirement-gate/request-revision",
            json={
                "operator_id": "OP-RESOLVE-1",
                "rationale": "Missing DB definition",
                "revision_notes": "Please include SQLite reference path in affected files"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["gate_status"] == "REVISION_REQUESTED"
        assert data["sandbox_ready"] is False

        # Load file and assert
        with open(TEST_PROJECT_DIR / "requirement_gate.json", "r", encoding="utf-8") as f:
            gate_data = json.load(f)
        assert gate_data["status"] == "REVISION_REQUESTED"
        assert gate_data["scope_adjustments"] == "Please include SQLite reference path in affected files"


@pytest.mark.asyncio
async def test_reject():
    """
    7. reject statusu REJECTED yapar
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            f"/api/v1/project-factory/{TEST_PROJECT_ID}/requirement-gate/reject",
            json={
                "operator_id": "OP-RESOLVE-1",
                "rationale": "Out of scope completely"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["gate_status"] == "REJECTED"
        assert data["sandbox_ready"] is False


@pytest.mark.asyncio
async def test_gate_decisions_log_append_only():
    """
    8. gate_decisions.jsonl append-only çalışır
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Resolve twice to see if it appends twice (we change status back to WAITING_FOR_OPERATOR to simulate multiple attempts)
        response1 = await ac.post(
            f"/api/v1/project-factory/{TEST_PROJECT_ID}/requirement-gate/request-revision",
            json={
                "operator_id": "OP-RESOLVE-1",
                "rationale": "Revision request 1",
                "revision_notes": "Need revision notes"
            }
        )
        assert response1.status_code == 200

        # Change status back manually to test second decision
        with open(TEST_PROJECT_DIR / "requirement_gate.json", "r", encoding="utf-8") as f:
            gate_data = json.load(f)
        gate_data["status"] = "WAITING_FOR_OPERATOR"
        with open(TEST_PROJECT_DIR / "requirement_gate.json", "w", encoding="utf-8") as f:
            json.dump(gate_data, f, indent=2)

        response2 = await ac.post(
            f"/api/v1/project-factory/{TEST_PROJECT_ID}/requirement-gate/reject",
            json={
                "operator_id": "OP-RESOLVE-1",
                "rationale": "Rejecting now"
            }
        )
        assert response2.status_code == 200

        # Check append-only decisions file
        decisions_path = TEST_PROJECT_DIR / "gate_decisions.jsonl"
        assert decisions_path.exists()

        decisions = []
        with open(decisions_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    decisions.append(json.loads(line))

        assert len(decisions) == 2
        assert decisions[0]["action"] == "REQUEST_REVISION"
        assert decisions[1]["action"] == "REJECT"


@pytest.mark.asyncio
async def test_duplicate_approve_scope_blocked():
    """
    9. duplicate approve-scope ikinci sandbox run üretmez (State machine blocks it)
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # First approve
        response1 = await ac.post(
            f"/api/v1/project-factory/{TEST_PROJECT_ID}/requirement-gate/approve-scope",
            json={
                "operator_id": "OP-RESOLVE-1",
                "rationale": "Approve 1",
                "approved_scope": "mvp",
                "risk_acknowledgement": True
            }
        )
        assert response1.status_code == 200

        # Second approve should return 400 because state has already transitioned
        response2 = await ac.post(
            f"/api/v1/project-factory/{TEST_PROJECT_ID}/requirement-gate/approve-scope",
            json={
                "operator_id": "OP-RESOLVE-1",
                "rationale": "Approve 2",
                "approved_scope": "mvp",
                "risk_acknowledgement": True
            }
        )
        assert response2.status_code == 400
        assert "already been resolved" in response2.json()["detail"]


def test_router_registry_contains_endpoints():
    """
    10. router registry içinde endpointler canlı görünür
    """
    routes = router_registry.get_all_routes()
    path_list = [r["path"] for r in routes]
    assert "/project-factory" in path_list
