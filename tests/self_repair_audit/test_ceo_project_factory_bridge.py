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

# Workspace Paths
WORKSPACE_ROOT = Path("e:/ai_company_faz12.1").resolve()
AUDIT_RUNS_DIR = WORKSPACE_ROOT / "project_outputs" / "audit_runs"
TEST_AUDIT_RUN_ID = "AUD-TEST-BRIDGE-PF-999"
TEST_RUN_DIR = AUDIT_RUNS_DIR / TEST_AUDIT_RUN_ID
PROJECT_FACTORY_BASE = WORKSPACE_ROOT / "project_outputs" / "project_factory"


@pytest.fixture(autouse=True)
async def setup_test_environment():
    print("\n>>> Entering setup_test_environment fixture for PF...", flush=True)

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

    # 2. Setup project output folder structure
    if TEST_RUN_DIR.exists():
        shutil.rmtree(TEST_RUN_DIR, ignore_errors=True)
    os.makedirs(TEST_RUN_DIR, exist_ok=True)

    # 3. Create dummy classified_findings.json
    findings_data = {
        "findings": [
            {
                "finding_id": "pf-bridge-info-1",
                "title": "Low Priority Diagnostic Finding for PF",
                "description": "A non-critical issue with system environment suitable for Project Factory.",
                "category": "frontend",
                "severity": "INFO",
                "priority_score": 10,
                "source": "api_contract_scanner",
                "status": "NEW",
                "affected_files": ["apps/refine_control_plane/src/app/page.tsx"],
                "affected_endpoint": "/api/v1/suggestions"
            },
            {
                "finding_id": "pf-bridge-critical-1",
                "title": "Critical Authentication Hole for PF",
                "description": "An open security issue suitable for Project Factory.",
                "category": "security",
                "severity": "CRITICAL",
                "priority_score": 95,
                "source": "security_guardrail_scanner",
                "status": "NEW",
                "affected_files": ["services/auth/jwt_auth.py"],
                "affected_endpoint": "/api/v1/ceo/suggestions"
            }
        ]
    }

    with open(TEST_RUN_DIR / "classified_findings.json", "w", encoding="utf-8") as f:
        json.dump(findings_data, f, indent=2)

    state_data = {
        "pf-bridge-info-1": "NEW",
        "pf-bridge-critical-1": "NEW"
    }
    with open(TEST_RUN_DIR / "suggestion_state.json", "w", encoding="utf-8") as f:
        json.dump(state_data, f, indent=2)

    print(">>> Finished fixture setup, yielding to test case...", flush=True)
    yield
    print("\n>>> Entering fixture teardown for PF...", flush=True)

    # Clean up generated audit files & outputs
    app.dependency_overrides.clear()
    if TEST_RUN_DIR.exists():
        shutil.rmtree(TEST_RUN_DIR, ignore_errors=True)

    # Clean up specific generated project directories
    if PROJECT_FACTORY_BASE.exists():
        shutil.rmtree(PROJECT_FACTORY_BASE / "PF-pf-bridge-info-1", ignore_errors=True)
        shutil.rmtree(PROJECT_FACTORY_BASE / "PF-pf-bridge-critical-1", ignore_errors=True)
    print(">>> Finished fixture teardown for PF.", flush=True)


@pytest.mark.asyncio
async def test_approve_project_factory_produces_artifacts_and_logs():
    """
    Verify that POST /suggestions/{suggestion_id}/approve-project-factory:
    - Generates project_brief.json and requirement_gate.json in project_outputs/project_factory/PF-{suggestion_id}/
    - Appends exactly two logs in suggestion_actions.jsonl (APPROVE_PROJECT_FACTORY & PROJECT_FACTORY_INTAKE_CREATED)
    - Updates suggestion state to REQUIREMENT_GATE_WAITING in suggestion_state.json
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            f"/api/v1/ceo/suggestions/pf-bridge-info-1/approve-project-factory?audit_run_id={TEST_AUDIT_RUN_ID}",
            json={
                "operator_id": "OP-TEST-PF-1",
                "rationale": "Approved for project factory test",
                "risk_acknowledgement": False
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "project_factory_run" in data
        assert data["project_factory_run"]["project_id"] == "PF-pf-bridge-info-1"
        assert data["project_factory_run"]["status"] == "REQUIREMENT_GATE_WAITING"

        # Check generated artifacts under project_outputs/project_factory/PF-pf-bridge-info-1
        project_dir = PROJECT_FACTORY_BASE / "PF-pf-bridge-info-1"
        assert project_dir.exists()

        brief_path = project_dir / "project_brief.json"
        assert brief_path.exists()
        with open(brief_path, "r", encoding="utf-8") as f:
            brief_data = json.load(f)
        assert brief_data["project_id"] == "PF-pf-bridge-info-1"
        assert brief_data["source_suggestion_id"] == "pf-bridge-info-1"
        assert brief_data["status"] == "REQUIREMENT_GATE_WAITING"

        gate_path = project_dir / "requirement_gate.json"
        assert gate_path.exists()
        with open(gate_path, "r", encoding="utf-8") as f:
            gate_data = json.load(f)
        assert gate_data["status"] == "WAITING_FOR_OPERATOR"
        assert gate_data["implementation_allowed"] is False

        # Assert append-only logs in suggestion_actions.jsonl (Exactly two logs)
        actions_file = TEST_RUN_DIR / "suggestion_actions.jsonl"
        assert actions_file.exists()

        logs = []
        with open(actions_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    logs.append(json.loads(line))

        assert len(logs) == 2
        assert logs[0]["action"] == "APPROVE_PROJECT_FACTORY"
        assert logs[0]["from_status"] == "NEW"
        assert logs[0]["to_status"] == "APPROVED_FOR_PROJECT_FACTORY"
        assert logs[0]["operator_id"] == "OP-TEST-PF-1"

        assert logs[1]["action"] == "PROJECT_FACTORY_INTAKE_CREATED"
        assert logs[1]["from_status"] == "APPROVED_FOR_PROJECT_FACTORY"
        assert logs[1]["to_status"] == "REQUIREMENT_GATE_WAITING"
        assert logs[1]["operator_id"] == "OP-TEST-PF-1"
        assert logs[1]["result"]["project_id"] == "PF-pf-bridge-info-1"

        # Check suggestion state has been updated to REQUIREMENT_GATE_WAITING
        state_file = TEST_RUN_DIR / "suggestion_state.json"
        with open(state_file, "r", encoding="utf-8") as f:
            states = json.load(f)
        assert states["pf-bridge-info-1"] == "REQUIREMENT_GATE_WAITING"


@pytest.mark.asyncio
async def test_approve_project_factory_risk_acknowledgement_enforcement():
    """
    Assert that operator risk acknowledgement is mandatory for CRITICAL findings in PF.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Trigger without risk_acknowledgement -> should fail with 400
        response_fail = await ac.post(
            f"/api/v1/ceo/suggestions/pf-bridge-critical-1/approve-project-factory?audit_run_id={TEST_AUDIT_RUN_ID}",
            json={
                "operator_id": "OP-TEST-PF-2",
                "rationale": "High priority project factory intake",
                "risk_acknowledgement": False
            }
        )
        assert response_fail.status_code == 400
        assert "Risk acknowledgement is mandatory" in response_fail.json()["detail"]

        # Trigger with risk_acknowledgement -> should succeed
        response_ok = await ac.post(
            f"/api/v1/ceo/suggestions/pf-bridge-critical-1/approve-project-factory?audit_run_id={TEST_AUDIT_RUN_ID}",
            json={
                "operator_id": "OP-TEST-PF-2",
                "rationale": "High priority project factory intake with caution",
                "risk_acknowledgement": True
            }
        )
        assert response_ok.status_code == 200
        data = response_ok.json()
        assert data["status"] == "success"
        assert data["project_factory_run"]["status"] == "REQUIREMENT_GATE_WAITING"


@pytest.mark.asyncio
async def test_approve_project_factory_prevent_duplicates():
    """
    Assert that repeating approval returns already_started status.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # First approval
        res1 = await ac.post(
            f"/api/v1/ceo/suggestions/pf-bridge-info-1/approve-project-factory?audit_run_id={TEST_AUDIT_RUN_ID}",
            json={
                "operator_id": "OP-TEST-PF-3",
                "rationale": "Initial approval",
                "risk_acknowledgement": False
            }
        )
        assert res1.status_code == 200

        # Second approval -> should yield already_started
        res2 = await ac.post(
            f"/api/v1/ceo/suggestions/pf-bridge-info-1/approve-project-factory?audit_run_id={TEST_AUDIT_RUN_ID}",
            json={
                "operator_id": "OP-TEST-PF-3",
                "rationale": "Initial approval duplication",
                "risk_acknowledgement": False
            }
        )
        assert res2.status_code == 200
        data = res2.json()
        assert data["status"] == "already_started"
        assert data["project_factory_run"]["project_id"] == "PF-pf-bridge-info-1"


@pytest.mark.asyncio
async def test_get_suggestions_enriches_project_factory_links(monkeypatch):
    """
    Verify GET /suggestions enriches the suggestions payload with project_factory_run metadata.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Start a project factory run
        approve_resp = await ac.post(
            f"/api/v1/ceo/suggestions/pf-bridge-info-1/approve-project-factory?audit_run_id={TEST_AUDIT_RUN_ID}",
            json={
                "operator_id": "OP-TEST-PF-4",
                "rationale": "Preparing connection link enrichment test for PF",
                "risk_acknowledgement": False
            }
        )
        assert approve_resp.status_code == 200

        # Monkeypatch CEO router to pick our custom TEST_AUDIT_RUN_ID
        import services.workflow_api.ceo_router as ceo_router_mod
        monkeypatch.setattr(ceo_router_mod, "_resolve_audit_run_id", lambda rid, wroot: TEST_AUDIT_RUN_ID)

        # Retrieve enriched suggestions list
        get_resp = await ac.get(f"/api/v1/ceo/suggestions?force_refresh=False")
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["status"] == "success"
        
        findings = data["findings"]
        target_finding = next((f for f in findings if f["finding_id"] == "pf-bridge-info-1"), None)
        assert target_finding is not None
        assert "project_factory_run" in target_finding
        run_data = target_finding["project_factory_run"]
        assert run_data["project_id"] == "PF-pf-bridge-info-1"
        assert run_data["status"] == "REQUIREMENT_GATE_WAITING"
