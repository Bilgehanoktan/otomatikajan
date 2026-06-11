from __future__ import annotations

import json
import os
import shutil
import pytest
from pathlib import Path
from httpx import AsyncClient, ASGITransport

from services.workflow_api.main import app
from services.taskflow.taskflow_engine import run_workflow
from services.repair.taskflow_artifacts import artifact_dir_for_run

# Workspace Root
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
REPAIR_OUTPUTS = WORKSPACE_ROOT / "repair_outputs"

@pytest.fixture(autouse=True)
def cleanup_outputs():
    """Ensure output directories are clean before and after each test."""
    yield
    if REPAIR_OUTPUTS.exists():
        for child in REPAIR_OUTPUTS.iterdir():
            if child.is_dir() and child.name.startswith("INC-INTFLOW-"):
                shutil.rmtree(child, ignore_errors=True)

@pytest.mark.asyncio
async def test_full_self_repair_artifact_flow_and_api():
    """Verify that a full taskflow run writes all step artifacts, generates a manifest, and responds correctly via the REST API."""
    incident_id = "INC-INTFLOW-99"
    
    # Standard input payload for the self_repair_v1 workflow
    input_payload = {
        "incident_id": incident_id,
        "trace_id": "trace-intflow-99",
        "error_type": "unit_test_failure",
        "summary": "FastAPI router integration failing.",
        "failed_command": "pytest tests/unit/test_repair_lab_improvements.py",
        "failed_test": "test_routing",
        "traceback": "Traceback (most recent call last):\n  File 'test_routing.py', line 12\nAssertionError"
    }
    
    # Run the workflow
    run = run_workflow("self_repair_v1", input_payload, output_root=REPAIR_OUTPUTS)
    
    # Ensure the run was completed or properly transitioned
    assert run.status in {"DRAFT_PR_READY", "COMPLETED", "WAITING_HUMAN", "FAILED"}
    
    # Verify the run directory is created
    run_dir = artifact_dir_for_run(incident_id, run.run_id, REPAIR_OUTPUTS)
    assert run_dir.exists()
    
    # Verify artifact_manifest.json exists on disk
    manifest_path = run_dir / "artifact_manifest.json"
    assert manifest_path.exists()
    
    # Load manifest and verify its contents
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
        
    assert manifest["workflow_id"] == "self_repair_v1"
    assert manifest["run_id"] == run.run_id
    assert manifest["incident_id"] == incident_id
    assert "artifacts" in manifest
    
    # The manifest should contain status and hash for the executed steps
    artifacts_dict = {art["name"]: art for art in manifest["artifacts"]}
    
    # Assert crucial Phase 4 artifacts
    assert "failure_context.json" in artifacts_dict
    assert "repair_case.json" in artifacts_dict
    assert "localization_report.json" in artifacts_dict
    assert "repair_plan.json" in artifacts_dict
    assert "patch_candidates.json" in artifacts_dict
    assert "sandbox_result.json" in artifacts_dict
    assert "verifier_mesh_result.json" in artifacts_dict
    assert "risk_report.json" in artifacts_dict
    
    assert artifacts_dict["failure_context.json"]["status"] == "written"
    assert artifacts_dict["failure_context.json"]["sha256"] is not None
    
    # ── Test the REST API Router ──────────────────────────────────────────────
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(f"/api/v1/repair-lab/runs/{run.run_id}/artifacts")
        assert response.status_code == 200
        
        data = response.json()
        assert data["workflow_id"] == "self_repair_v1"
        assert data["run_id"] == run.run_id
        assert data["incident_id"] == incident_id
        
        # Verify retrieved artifacts
        retrieved_artifacts = {art["name"]: art for art in data["artifacts"]}
        assert "failure_context.json" in retrieved_artifacts
        assert retrieved_artifacts["failure_context.json"]["status"] == "written"
        
        # Test 404 for non-existent run_id
        response_404 = await ac.get("/api/v1/repair-lab/runs/non-existent-run-id/artifacts")
        assert response_404.status_code == 404
