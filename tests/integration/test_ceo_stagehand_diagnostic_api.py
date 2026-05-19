from __future__ import annotations

import json
import shutil
import uuid
import pytest
from pathlib import Path
from httpx import AsyncClient, ASGITransport

from services.workflow_api.main import app
from services.auth.jwt_auth import get_current_identity, require_permission

WORKSPACE_ROOT = Path("e:/ai_company_faz12.1").resolve()
REPAIR_OUTPUTS = WORKSPACE_ROOT / "repair_outputs"
DIAGNOSTICS_DIR = REPAIR_OUTPUTS / "diagnostics"

@pytest.fixture(autouse=True)
def clean_diagnostics_and_incidents():
    """Ensure clean diagnostic and incident directories before and after each test."""
    yield
    if DIAGNOSTICS_DIR.exists():
        shutil.rmtree(DIAGNOSTICS_DIR, ignore_errors=True)
    if REPAIR_OUTPUTS.exists():
        for child in REPAIR_OUTPUTS.iterdir():
            if child.is_dir() and child.name.startswith("INC-CEO-"):
                shutil.rmtree(child, ignore_errors=True)

@pytest.fixture
def auth_overrides():
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
    yield
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_post_stagehand_diagnostic_returns_finding_payload(auth_overrides):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "route": "/ceo",
            "symptom": "Findings table is empty",
            "expected_endpoint": "/api/v1/ceo/findings",
            "mode": "mock"
        }
        response = await ac.post("/api/v1/ceo/diagnostics/stagehand", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "created"
        assert data["diagnostic_id"].startswith("DIAG-")
        assert "diagnostic_report.json" in data["artifact_ref"]
        
        finding = data["finding"]
        assert finding["finding_id"] == data["diagnostic_id"]
        assert finding["category"] == "ui_diagnostic"
        assert finding["priority_score"] == 78
        assert finding["affected_route"] == "/ceo"
        assert finding["affected_endpoint"] == "/api/v1/ceo/findings"
        assert finding["recommended_agent"] == "swe_agent"
        assert finding["requested_mode"] == "local_adapter"

@pytest.mark.asyncio
async def test_post_stagehand_diagnostic_writes_artifact(auth_overrides):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "route": "/identity-trust",
            "symptom": "Hydration mismatch in trust panel",
            "expected_endpoint": "/api/v1/trust/verify",
            "mode": "mock"
        }
        response = await ac.post("/api/v1/ceo/diagnostics/stagehand", json=payload)
        assert response.status_code == 200
        data = response.json()
        diagnostic_id = data["diagnostic_id"]
        
        # Verify folder and files exist
        diag_dir = DIAGNOSTICS_DIR / diagnostic_id
        assert diag_dir.exists()
        assert (diag_dir / "diagnostic_report.json").exists()
        assert (diag_dir / "network_log.json").exists()
        assert (diag_dir / "console_log.json").exists()
        assert (diag_dir / "screenshot.png").exists()

@pytest.mark.asyncio
async def test_get_repair_lab_diagnostic_returns_report(auth_overrides):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Create diagnostic
        payload = {
            "route": "/ceo",
            "symptom": "regular responsive test",
            "expected_endpoint": None,
            "mode": "mock"
        }
        response = await ac.post("/api/v1/ceo/diagnostics/stagehand", json=payload)
        assert response.status_code == 200
        diagnostic_id = response.json()["diagnostic_id"]
        
        # 2. Get diagnostic
        get_response = await ac.get(f"/api/v1/repair-lab/diagnostics/{diagnostic_id}")
        assert get_response.status_code == 200
        diag_data = get_response.json()
        assert diag_data["diagnostic_id"] == diagnostic_id
        assert diag_data["route"] == "/ceo"
        assert diag_data["symptom"] == "regular responsive test"
        
        # 3. 404 checks
        not_found_response = await ac.get("/api/v1/repair-lab/diagnostics/DIAG-NONEXIST")
        assert not_found_response.status_code == 404
        
        # 4. Path traversal defense check
        traversal_response = await ac.get("/api/v1/repair-lab/diagnostics/..%5Chack")
        assert traversal_response.status_code == 400

@pytest.mark.asyncio
async def test_stagehand_diagnostic_can_be_used_to_create_repair_case(auth_overrides):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Run diagnostic to get finding
        diag_payload = {
            "route": "/ceo",
            "symptom": "findings table is empty",
            "expected_endpoint": "/api/v1/ceo/findings",
            "mode": "mock"
        }
        diag_res = await ac.post("/api/v1/ceo/diagnostics/stagehand", json=diag_payload)
        assert diag_res.status_code == 200
        finding = diag_res.json()["finding"]
        finding_id = diag_res.json()["diagnostic_id"]
        
        # 2. Bridge diagnostic finding to repair case
        bridge_payload = {
            "finding": finding,
            "auto_start": False
        }
        bridge_res = await ac.post(
            f"/api/v1/ceo/findings/{finding_id}/repair-case",
            json=bridge_payload
        )
        assert bridge_res.status_code == 200
        bridge_data = bridge_res.json()
        
        assert bridge_data["status"] == "created"
        assert bridge_data["finding_id"] == finding_id
        assert bridge_data["next_step"] == "start_self_repair_taskflow"
        
        incident_id = bridge_data["incident_id"]
        repair_case_path = REPAIR_OUTPUTS / incident_id / "repair_case.json"
        assert repair_case_path.exists()
        
        case_data = json.loads(repair_case_path.read_text(encoding="utf-8"))
        assert case_data["finding_id"] == finding_id
        assert case_data["affected_route"] == "/ceo"
        assert case_data["affected_endpoint"] == "/api/v1/ceo/findings"
        assert "services/workflow_api/ceo_router.py" in case_data["affected_files"]
