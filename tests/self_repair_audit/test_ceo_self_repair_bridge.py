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
from libs.db.session import get_db_ctx
from libs.db.repositories.repository import ProjectRepository

# Workspace Paths
WORKSPACE_ROOT = Path("e:/ai_company_faz12.1").resolve()
AUDIT_RUNS_DIR = WORKSPACE_ROOT / "project_outputs" / "audit_runs"
TEST_AUDIT_RUN_ID = "AUD-TEST-BRIDGE-999"
TEST_RUN_DIR = AUDIT_RUNS_DIR / TEST_AUDIT_RUN_ID
REPAIR_OUTPUTS = WORKSPACE_ROOT / "repair_outputs"


@pytest.fixture(autouse=True)
async def setup_test_environment(monkeypatch):
    print("\n>>> Entering setup_test_environment fixture...", flush=True)
    
    # Mock the job queue to prevent running actual Celery/Redis tasks or heavy in-process workers
    from services.orchestration.application.job_queue import job_queue, Job
    
    async def mock_enqueue(job_type, **payload):
        mock_job_id = f"job-{uuid.uuid4().hex[:8]}"
        print(f">>> Mock job_queue.enqueue called. ID: {mock_job_id}", flush=True)
        return Job(
            id=mock_job_id,
            type=job_type,
            payload=payload,
            status="queued"
        )
        
    async def mock_start(num_workers=2):
        print(">>> Mock job_queue.start called, doing nothing...", flush=True)
        job_queue._running = True
        
    async def mock_stop():
        print(">>> Mock job_queue.stop called, doing nothing...", flush=True)
        job_queue._running = False
        
    monkeypatch.setattr(job_queue, "enqueue", mock_enqueue)
    monkeypatch.setattr(job_queue, "start", mock_start)
    monkeypatch.setattr(job_queue, "stop", mock_stop)

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

    # 3. Create dummy classified_findings.json with INFO and CRITICAL findings
    findings_data = {
        "findings": [
            {
                "finding_id": "bridge-info-1",
                "title": "Low Priority Diagnostic Finding",
                "description": "A non-critical issue with system environment.",
                "category": "frontend",
                "severity": "INFO",
                "priority_score": 10,
                "source": "api_contract_scanner",
                "status": "NEW",
                "affected_files": ["apps/refine_control_plane/src/app/page.tsx"],
                "affected_endpoint": "/api/v1/suggestions"
            },
            {
                "finding_id": "bridge-critical-1",
                "title": "Critical Authentication Hole",
                "description": "An open security issue that bypasses token checks.",
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
    
    # Write classified_findings.json
    with open(TEST_RUN_DIR / "classified_findings.json", "w", encoding="utf-8") as f:
        json.dump(findings_data, f, indent=2)

    # Create dummy suggestion_state.json with default statuses
    state_data = {
        "bridge-info-1": "NEW",
        "bridge-critical-1": "NEW"
    }
    with open(TEST_RUN_DIR / "suggestion_state.json", "w", encoding="utf-8") as f:
        json.dump(state_data, f, indent=2)

    print(">>> Finished fixture setup, yielding to test case...", flush=True)
    yield
    print("\n>>> Entering fixture teardown...", flush=True)

    # Clean up generated audit files & outputs
    app.dependency_overrides.clear()
    if TEST_RUN_DIR.exists():
        shutil.rmtree(TEST_RUN_DIR, ignore_errors=True)
    
    if REPAIR_OUTPUTS.exists():
        for child in REPAIR_OUTPUTS.iterdir():
            if child.is_dir() and child.name.startswith("INC-CEO-"):
                shutil.rmtree(child, ignore_errors=True)
    print(">>> Finished fixture teardown.", flush=True)


@pytest.mark.asyncio
async def test_approve_self_repair_produces_artifacts_and_enqueues_project():
    """
    Verify that POST /suggestions/{suggestion_id}/approve-self-repair:
    - Generates a correct repair_case.json and taskflow_run.json artifact in repair_outputs/INC-CEO-*/
    - Inserts a high-priority Project in the database and enqueues the Job
    - Appends exactly two logs in suggestion_actions.jsonl (APPROVE_SELF_REPAIR & SELF_REPAIR_STARTED)
    - Automatically updates the suggestion state in suggestion_state.json to IN_PROGRESS
    """
    print("\n>>> Inside test_approve_self_repair_produces_artifacts_and_enqueues_project...", flush=True)
    transport = ASGITransport(app=app)
    print(">>> ASGITransport created, entering AsyncClient context...", flush=True)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        
        # 1. Trigger approve-self-repair on info finding
        print(">>> Making POST request to approve-self-repair...", flush=True)
        response = await ac.post(
            f"/api/v1/ceo/suggestions/bridge-info-1/approve-self-repair?audit_run_id={TEST_AUDIT_RUN_ID}",
            json={
                "operator_id": "OP-TEST-1",
                "rationale": "Approved for self-repair test",
                "risk_acknowledgement": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "repair_run" in data
        assert "taskflow_id" in data["repair_run"]
        assert "job_id" in data["repair_run"]
        assert data["repair_run"]["status"] == "QUEUED"
        
        taskflow_id = data["repair_run"]["taskflow_id"]
        job_id = data["repair_run"]["job_id"]
        incident_id = data["repair_run"]["incident_id"]
        
        # 2. Check generated artifacts under repair_outputs/INC-CEO-*
        incident_dir = REPAIR_OUTPUTS / incident_id
        assert incident_dir.exists()
        
        # Verify repair_case.json
        repair_case_path = incident_dir / "repair_case.json"
        assert repair_case_path.exists()
        with open(repair_case_path, "r", encoding="utf-8") as f:
            case_data = json.load(f)
        assert case_data["finding_id"] == "bridge-info-1"
        assert case_data["incident_id"] == incident_id
        assert case_data["affected_files"] == ["apps/refine_control_plane/src/app/page.tsx"]
        assert case_data["recommended_agent"] == "swe_agent"
        
        # Verify taskflow_run.json
        taskflow_run_path = incident_dir / "taskflow_run.json"
        assert taskflow_run_path.exists()
        with open(taskflow_run_path, "r", encoding="utf-8") as f:
            run_data = json.load(f)
        assert run_data["project_id"] == taskflow_id
        assert run_data["job_id"] == job_id
        assert run_data["status"] == "queued"
        
        # 3. Verify Project database record is created using repositories
        async with get_db_ctx() as session:
            project = await ProjectRepository.get(session, taskflow_id)
            assert project is not None
            assert project.title == f"Self Repair Case: {incident_id}"
            assert project.workflow_template == "self_repair"
            assert project.status == "QUEUED"
            assert project.job_id == job_id
            assert project.execution_context["finding_id"] == "bridge-info-1"
            
        # 4. Assert append-only logs in suggestion_actions.jsonl (Exactly two logs)
        actions_file = TEST_RUN_DIR / "suggestion_actions.jsonl"
        assert actions_file.exists()
        
        logs = []
        with open(actions_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    logs.append(json.loads(line))
                    
        assert len(logs) == 2
        
        # First log: APPROVE_SELF_REPAIR
        assert logs[0]["action"] == "APPROVE_SELF_REPAIR"
        assert logs[0]["from_status"] == "NEW"
        assert logs[0]["to_status"] == "APPROVED_FOR_REPAIR"
        assert logs[0]["operator_id"] == "OP-TEST-1"
        
        # Second log: SELF_REPAIR_STARTED
        assert logs[1]["action"] == "SELF_REPAIR_STARTED"
        assert logs[1]["from_status"] == "APPROVED_FOR_REPAIR"
        assert logs[1]["to_status"] == "IN_PROGRESS"
        assert logs[1]["operator_id"] == "OP-TEST-1"
        assert logs[1]["result"]["taskflow_id"] == taskflow_id
        assert logs[1]["result"]["job_id"] == job_id
        
        # 5. Check if suggestion state has been updated to IN_PROGRESS in suggestion_state.json
        state_file = TEST_RUN_DIR / "suggestion_state.json"
        with open(state_file, "r", encoding="utf-8") as f:
            states = json.load(f)
        assert states["bridge-info-1"] == "IN_PROGRESS"


@pytest.mark.asyncio
async def test_approve_self_repair_risk_acknowledgement_enforcement():
    """
    Assert that operator risk acknowledgement is mandatory for CRITICAL findings.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        
        # 1. Trigger without risk_acknowledgement -> should fail with 400
        response_fail = await ac.post(
            f"/api/v1/ceo/suggestions/bridge-critical-1/approve-self-repair?audit_run_id={TEST_AUDIT_RUN_ID}",
            json={
                "operator_id": "OP-TEST-2",
                "rationale": "High priority security fix",
                "risk_acknowledgement": False
            }
        )
        assert response_fail.status_code == 400
        assert "Risk acknowledgement is mandatory" in response_fail.json()["detail"]
        
        # 2. Trigger with risk_acknowledgement -> should succeed
        response_ok = await ac.post(
            f"/api/v1/ceo/suggestions/bridge-critical-1/approve-self-repair?audit_run_id={TEST_AUDIT_RUN_ID}",
            json={
                "operator_id": "OP-TEST-2",
                "rationale": "High priority security fix with caution",
                "risk_acknowledgement": True
            }
        )
        assert response_ok.status_code == 200
        data = response_ok.json()
        assert data["status"] == "success"
        assert data["repair_run"]["status"] == "QUEUED"


@pytest.mark.asyncio
async def test_get_suggestions_enriches_live_run_details(monkeypatch):
    """
    Verify that GET /suggestions properly reads run link snapshots, queries the db,
    and enriches suggestions with active run metadata parameters.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        
        # 1. Start a self-repair to create active connection links
        approve_resp = await ac.post(
            f"/api/v1/ceo/suggestions/bridge-info-1/approve-self-repair?audit_run_id={TEST_AUDIT_RUN_ID}",
            json={
                "operator_id": "OP-TEST-3",
                "rationale": "Preparing connection link enrichment test",
                "risk_acknowledgement": False
            }
        )
        assert approve_resp.status_code == 200
        run_info = approve_resp.json()["repair_run"]
        taskflow_id = run_info["taskflow_id"]
        job_id = run_info["job_id"]
        incident_id = run_info["incident_id"]
        
        # Mock monkeypatch search paths to pick our custom TEST_AUDIT_RUN_ID
        import services.workflow_api.ceo_router as ceo_router_mod
        original_resolve = ceo_router_mod._resolve_audit_run_id
        monkeypatch.setattr(ceo_router_mod, "_resolve_audit_run_id", lambda rid, wroot: TEST_AUDIT_RUN_ID)
        
        # Mock os.listdir in ceo_router to return our TEST_AUDIT_RUN_ID
        original_listdir = os.listdir
        def mock_listdir(path):
            if "audit_runs" in str(path):
                return [TEST_AUDIT_RUN_ID]
            return original_listdir(path)
        monkeypatch.setattr(os, "listdir", mock_listdir)
        
        # 2. Retrieve suggestions and verify enrichment
        response = await ac.get(f"/api/v1/ceo/suggestions?force_refresh=false")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["audit_run_id"] == TEST_AUDIT_RUN_ID
        
        findings = data["findings"]
        info_finding = next(f for f in findings if f["finding_id"] == "bridge-info-1")
        
        assert info_finding["status"] == "IN_PROGRESS"
        assert "repair_run" in info_finding
        assert info_finding["repair_run"]["taskflow_id"] == taskflow_id
        assert info_finding["repair_run"]["job_id"] == job_id
        assert info_finding["repair_run"]["incident_id"] == incident_id
        assert info_finding["repair_run"]["status"] in ("QUEUED", "RUNNING")
        assert info_finding["repair_run"]["workflow_url"] == f"/workflows/{taskflow_id}"


@pytest.mark.asyncio
async def test_prevent_duplicate_runs_blocks_re_execution():
    """
    Verify that trying to trigger a run twice returns status: "already_started" with the original run metadata.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        
        # 1. Trigger first run
        first_resp = await ac.post(
            f"/api/v1/ceo/suggestions/bridge-info-1/approve-self-repair?audit_run_id={TEST_AUDIT_RUN_ID}",
            json={
                "operator_id": "OP-DUPLICATE-CHECK",
                "rationale": "Initial trigger",
                "risk_acknowledgement": False
            }
        )
        assert first_resp.status_code == 200
        first_data = first_resp.json()
        assert first_data["status"] == "success"
        taskflow_id = first_data["repair_run"]["taskflow_id"]
        job_id = first_data["repair_run"]["job_id"]
        
        # 2. Trigger second run (must be blocked as already_started)
        second_resp = await ac.post(
            f"/api/v1/ceo/suggestions/bridge-info-1/approve-self-repair?audit_run_id={TEST_AUDIT_RUN_ID}",
            json={
                "operator_id": "OP-DUPLICATE-CHECK",
                "rationale": "Second trigger attempt",
                "risk_acknowledgement": False
            }
        )
        assert second_resp.status_code == 200
        second_data = second_resp.json()
        assert second_data["status"] == "already_started"
        assert "repair_run" in second_data
        assert second_data["repair_run"]["taskflow_id"] == taskflow_id
        assert second_data["repair_run"]["job_id"] == job_id
        assert "workflow_url" in second_data["repair_run"]
