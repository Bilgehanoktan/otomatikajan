from __future__ import annotations

import json
import os
import shutil
import uuid
from pathlib import Path
import pytest
from httpx import AsyncClient, ASGITransport

from services.workflow_api.main import app
from services.auth.jwt_auth import get_current_identity, require_permission
from services.project_factory.models import ProjectFactoryIntake, RequirementGate
from services.project_factory.artifacts import write_project_factory_artifacts, _resolve_project_dir
from services.project_factory.delivery_packager import build_delivery_package, load_delivery_manifest

WORKSPACE_ROOT = Path("e:/ai_company_faz12.1").resolve()
TEST_PROJECT_ID = "PF-TEST-DEL-333"
TEST_PROJECT_DIR = WORKSPACE_ROOT / "project_outputs" / "project_factory" / TEST_PROJECT_ID

@pytest.fixture(autouse=True)
async def setup_test_environment():
    # 1. Setup authentication overrides
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

    # 2. Setup project outputs base folder
    if TEST_PROJECT_DIR.exists():
        shutil.rmtree(TEST_PROJECT_DIR, ignore_errors=True)
    TEST_PROJECT_DIR.mkdir(parents=True, exist_ok=True)

    # Write initial brief and requirement gate status
    intake = ProjectFactoryIntake(
        project_id=TEST_PROJECT_ID,
        source_suggestion_id="sug-del-333",
        audit_run_id="AUD-DEL-333",
        title="Test Delivery Package",
        problem_statement="Testing package building",
        recommended_action="Execute delivery build",
        affected_files=["app/main.py"],
        status="DELIVERY_PACKAGE_READY"
    )
    gate = RequirementGate(
        gate="Requirement Approval Gate",
        status="DELIVERY_PACKAGE_READY",
        allowed_actions=["approve_scope", "request_revision", "reject"]
    )
    write_project_factory_artifacts(intake, gate, str(WORKSPACE_ROOT))

    # Scaffold mock files needed for review checks
    manifest_data = {
        "project_id": TEST_PROJECT_ID,
        "candidate_id": "CAND-PF-333",
        "status": "CANDIDATE_READY",
        "files": [{"path": "app/main.py", "checksum": "abc123main"}]
    }
    with open(TEST_PROJECT_DIR / "candidate_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest_data, f)

    with open(TEST_PROJECT_DIR / "verification_report.json", "w", encoding="utf-8") as f:
        json.dump({"status": "PASSED"}, f)

    with open(TEST_PROJECT_DIR / "quality_scorecard.json", "w", encoding="utf-8") as f:
        json.dump({"score": 100}, f)

    with open(TEST_PROJECT_DIR / "risk_assessment.json", "w", encoding="utf-8") as f:
        json.dump({"risk_score": 10}, f)

    with open(TEST_PROJECT_DIR / "candidate_review.json", "w", encoding="utf-8") as f:
        json.dump({"status": "CANDIDATE_REVIEWED"}, f)

    # Create candidate package directory
    cand_dir = TEST_PROJECT_DIR / "candidate_package"
    cand_dir.mkdir(parents=True, exist_ok=True)
    os.makedirs(cand_dir / "app", exist_ok=True)
    with open(cand_dir / "app" / "main.py", "w", encoding="utf-8") as f:
        f.write("print('hello packaged')\n")

    yield

    # Cleanup
    app.dependency_overrides.clear()
    if TEST_PROJECT_DIR.exists():
        shutil.rmtree(TEST_PROJECT_DIR, ignore_errors=True)


def test_build_delivery_package_correctness():
    """
    Verifies that build_delivery_package successfully copies files, structures the manifest and locks apply permissions.
    """
    manifest = build_delivery_package(
        project_id=TEST_PROJECT_ID,
        operator_id="OP-DEL-1",
        rationale="Building packaging outputs",
        workspace_root=str(WORKSPACE_ROOT)
    )

    assert manifest["project_id"] == TEST_PROJECT_ID
    assert manifest["approved_by"] == "OP-DEL-1"
    assert manifest["production_apply_allowed"] is False
    assert len(manifest["files"]) == 1
    assert manifest["files"][0]["path"] == "files/app/main.py"

    # Verify that delivery files exist in physical delivery_package directory
    del_dir = TEST_PROJECT_DIR / "delivery_package"
    assert (del_dir / "files" / "app" / "main.py").exists()
    assert (del_dir / "delivery_manifest.json").exists()
    assert (del_dir / "release_notes.md").exists()

    # Load from disk
    loaded = load_delivery_manifest(TEST_PROJECT_ID, str(WORKSPACE_ROOT))
    assert loaded is not None
    assert loaded["delivery_id"] == manifest["delivery_id"]


@pytest.mark.asyncio
async def test_get_delivery_package_endpoint():
    """
    Verifies GET endpoint to retrieve packaged assets manifest and release notes content.
    """
    # Run backend delivery package builder first
    build_delivery_package(
        project_id=TEST_PROJECT_ID,
        operator_id="OP-DEL-1",
        rationale="Ready to deploy to staging.",
        workspace_root=str(WORKSPACE_ROOT)
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(f"/api/v1/project-factory/{TEST_PROJECT_ID}/delivery-package")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["delivery_manifest"]["approved_by"] == "OP-DEL-1"
        assert data["delivery_manifest"]["production_apply_allowed"] is False
        assert "release_notes" in data
        assert "Ready to deploy to staging." in data["release_notes"]
        assert "Direct production applying is strictly disabled" in data["release_notes"]
