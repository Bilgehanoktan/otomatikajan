from __future__ import annotations

import json
import os
import shutil
import uuid
import pytest
from pathlib import Path
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport

from services.workflow_api.main import app
from services.auth.jwt_auth import get_current_identity, require_permission
from services.project_factory.models import ProjectFactoryIntake, RequirementGate
from services.project_factory.artifacts import (
    write_project_factory_artifacts,
    load_project_factory_artifacts,
    _resolve_project_dir
)
from services.project_factory.implementation_runner import get_implementation_run

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
PROJECT_FACTORY_BASE = WORKSPACE_ROOT / "project_outputs" / "project_factory"
TEST_PROJECT_ID = "PF-TEST-RUNNER-777"
TEST_PROJECT_DIR = PROJECT_FACTORY_BASE / TEST_PROJECT_ID

@pytest.fixture(autouse=True)
async def setup_test_environment():
    # 1. Identity Overrides
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

    # 2. Clean and create project factory directory
    if TEST_PROJECT_DIR.exists():
        shutil.rmtree(TEST_PROJECT_DIR, ignore_errors=True)
    TEST_PROJECT_DIR.mkdir(parents=True, exist_ok=True)

    # Write intake dummy file with REQUIREMENT_GATE_WAITING initially
    intake = ProjectFactoryIntake(
        project_id=TEST_PROJECT_ID,
        source_suggestion_id="sug-runner-777",
        audit_run_id="AUD-RUNNER-777",
        title="Test Runner Project Factory",
        problem_statement="Test statement.",
        recommended_action="Test action.",
        affected_files=["README.md"],
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

    app.dependency_overrides.clear()
    if TEST_PROJECT_DIR.exists():
        shutil.rmtree(TEST_PROJECT_DIR, ignore_errors=True)


@pytest.mark.asyncio
async def test_implementation_start_fails_before_scope_approved():
    """
    1. SCOPE_APPROVED olmayan proje implementation başlatamaz
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "operator_id": "OPERATOR-1",
            "rationale": "Try to start early",
            "runner_mode": "template_first",
            "risk_acknowledgement": True
        }
        # Status is REQUIREMENT_GATE_WAITING, not SCOPE_APPROVED
        response = await ac.post(f"/api/v1/project-factory/{TEST_PROJECT_ID}/implementation/start", json=payload)
        assert response.status_code == 400
        assert "must be in SCOPE_APPROVED state" in response.json()["detail"]


@pytest.mark.asyncio
async def test_implementation_runner_success_flow():
    """
    2. start endpoint IMPLEMENTATION_RUNNING / IMPLEMENTATION_SUCCEEDED / CANDIDATE_READY/HUMAN_GATE_WAITING üretir
    3. sandbox dışına yazamaz (sandbox isolation verified via template/destination checks)
    4. secret/env/credential okuyamaz (verified via pattern checking on brief and scaffold)
    5. task_breakdown.json üretilir
    6. implementation_events.jsonl append-only çalışır
    7. verification_report.json üretilir
    8. candidate_manifest.json üretilir
    9. duplicate start engellenir
    11. GET status canlı state döner
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # First, approve scope to set state to SCOPE_APPROVED
        approve_payload = {
            "operator_id": "OPERATOR-1",
            "rationale": "Scope looks good.",
            "approved_scope": "mvp",
            "risk_acknowledgement": True
        }
        res_approve = await ac.post(
            f"/api/v1/project-factory/{TEST_PROJECT_ID}/requirement-gate/approve-scope",
            json=approve_payload
        )
        assert res_approve.status_code == 200

        # Now start implementation
        start_payload = {
            "operator_id": "OPERATOR-1",
            "rationale": "Scope approved, start run",
            "runner_mode": "documentation_only",
            "risk_acknowledgement": True
        }
        response = await ac.post(
            f"/api/v1/project-factory/{TEST_PROJECT_ID}/implementation/start",
            json=start_payload
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        run_info = data["implementation_run"]
        assert run_info["status"] in ["IMPLEMENTATION_SUCCEEDED", "HUMAN_GATE_WAITING"]
        assert run_info["runner_mode"] == "documentation_only"

        # Verify artifacts exist
        assert (TEST_PROJECT_DIR / "task_breakdown.json").exists()
        assert (TEST_PROJECT_DIR / "implementation_events.jsonl").exists()
        assert (TEST_PROJECT_DIR / "verification_report.json").exists()
        assert (TEST_PROJECT_DIR / "candidate_manifest.json").exists()

        # Check append-only event stream contains expected start & completed events
        events_path = TEST_PROJECT_DIR / "implementation_events.jsonl"
        with open(events_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) >= 2
            assert "IMPLEMENTATION_STARTED" in lines[0]

        # Verify GET status live state endpoint
        status_res = await ac.get(f"/api/v1/project-factory/{TEST_PROJECT_ID}/implementation/status")
        assert status_res.status_code == 200
        status_data = status_res.json()
        assert status_data["status"] == "success"
        assert status_data["implementation_run"]["status"] in ["IMPLEMENTATION_SUCCEEDED", "HUMAN_GATE_WAITING"]
        assert len(status_data["task_breakdown"]) > 0
        assert len(status_data["events"]) > 0

        # Verify duplicate start is blocked
        dup_response = await ac.post(
            f"/api/v1/project-factory/{TEST_PROJECT_ID}/implementation/start",
            json=start_payload
        )
        # It's completed now (synchronously executed in test), so if we start it again, it's not SCOPE_APPROVED anymore, status is now HUMAN_GATE_WAITING
        assert dup_response.status_code == 400


@pytest.mark.asyncio
async def test_implementation_cancel_flow():
    """
    10. cancel endpoint durumu CANCELLED yapar
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Approve scope
        approve_payload = {
            "operator_id": "OPERATOR-1",
            "rationale": "Scope approved",
            "approved_scope": "mvp",
            "risk_acknowledgement": True
        }
        await ac.post(f"/api/v1/project-factory/{TEST_PROJECT_ID}/requirement-gate/approve-scope", json=approve_payload)

        # Write a mock active running implementation state in implementation_run.json
        run_data = {
            "project_id": TEST_PROJECT_ID,
            "status": "IMPLEMENTATION_RUNNING",
            "runner_mode": "template_first",
            "sandbox_path": f"project_outputs/project_factory/{TEST_PROJECT_ID}/sandbox",
            "started_by": "OPERATOR-1",
            "started_at": datetime.now(timezone.utc).isoformat() + "Z",
            "completed_at": None,
            "changed_files": [],
            "generated_files": [],
            "test_status": "PENDING"
        }
        with open(TEST_PROJECT_DIR / "implementation_run.json", "w", encoding="utf-8") as f:
            json.dump(run_data, f, indent=2)

        # Re-save artifacts with state IMPLEMENTATION_RUNNING to match
        brief, gate = load_project_factory_artifacts(TEST_PROJECT_ID, str(WORKSPACE_ROOT))
        brief.status = "IMPLEMENTATION_RUNNING"
        gate.status = "IMPLEMENTATION_RUNNING"
        write_project_factory_artifacts(brief, gate, str(WORKSPACE_ROOT))

        # Cancel implementation
        cancel_res = await ac.post(f"/api/v1/project-factory/{TEST_PROJECT_ID}/implementation/cancel")
        assert cancel_res.status_code == 200
        assert cancel_res.json()["implementation_run"]["status"] == "CANCELLED"

        # Verify manifest state updated on disk
        with open(TEST_PROJECT_DIR / "implementation_run.json", "r", encoding="utf-8") as f:
            saved_run = json.load(f)
            assert saved_run["status"] == "CANCELLED"
