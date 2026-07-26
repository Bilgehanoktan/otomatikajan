from __future__ import annotations

import json
import shutil
import hashlib
import pytest
from pathlib import Path
from httpx import AsyncClient, ASGITransport

from services.workflow_api.main import app

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
REPAIR_OUTPUTS = WORKSPACE_ROOT / "repair_outputs"

@pytest.fixture
def setup_mock_run():
    run_id = "test-run-phase10"
    incident_id = "INC-TEST-PHASE10"
    
    run_dir = REPAIR_OUTPUTS / incident_id / "taskflow" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    
    # We will only write some of the artifacts to trigger partial blocking
    # and verify the API correctly detects blocking/missing artifacts
    manifest = {}
    
    # Let's write just one required artifact
    tour_payload = {"selected_candidate_id": "cand-001"}
    tour_file = run_dir / "tournament_result.json"
    tour_file.write_text(json.dumps(tour_payload), encoding="utf-8")
    
    sha = hashlib.sha256(json.dumps(tour_payload).encode("utf-8")).hexdigest()
    manifest["tournament_result.json"] = {"sha256": sha}
    
    (run_dir / "artifact_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    
    yield {
        "run_id": run_id,
        "incident_id": incident_id,
        "run_dir": run_dir
    }
    
    shutil.rmtree(REPAIR_OUTPUTS / incident_id, ignore_errors=True)


@pytest.mark.asyncio
async def test_get_release_readiness_contracts_returns_matrix():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/repair-lab/release-readiness/contracts")
        assert response.status_code == 200
        data = response.json()
        assert "api_routes" in data
        assert "artifact_schemas" in data
        assert len(data["api_routes"]) > 0


@pytest.mark.asyncio
async def test_post_release_readiness_check_writes_latest_report(setup_mock_run):
    run_id = setup_mock_run["run_id"]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/repair-lab/release-readiness/check",
            json={"run_id": run_id}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify the report has correct structure
        assert "status" in data
        assert "blocking_count" in data
        assert "checked_at" in data
        assert len(data["api_contracts"]) > 0
        
        # Verify persisted report
        report_file = REPAIR_OUTPUTS / "release_readiness" / "latest_report.json"
        assert report_file.exists()
        persisted = json.loads(report_file.read_text(encoding="utf-8"))
        assert persisted["status"] == data["status"]


@pytest.mark.asyncio
async def test_release_readiness_api_is_read_only(setup_mock_run):
    # Both GET and POST checks must be read-only (meaning they do not alter the database
    # or start executions, just report on the state of files and routing)
    run_id = setup_mock_run["run_id"]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response_get = await ac.get(f"/api/v1/repair-lab/release-readiness?run_id={run_id}")
        assert response_get.status_code == 200
        
        response_post = await ac.post(
            "/api/v1/repair-lab/release-readiness/check",
            json={"run_id": run_id}
        )
        assert response_post.status_code == 200
        
        # Verify both yielded identical status evaluations
        assert response_get.json()["status"] == response_post.json()["status"]


@pytest.mark.asyncio
async def test_release_readiness_reports_blocking_missing_artifact(setup_mock_run):
    run_id = setup_mock_run["run_id"]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/repair-lab/release-readiness/check",
            json={"run_id": run_id}
        )
        assert response.status_code == 200
        data = response.json()
        # Since setup_mock_run did not create all required artifacts (e.g. repair_case.json)
        # the status must be BLOCKED.
        assert data["status"] == "BLOCKED"
        assert data["blocking_count"] > 0
        
        # Confirm that repair_case.json is identified as a blocker
        artifact_contracts = data["artifact_contracts"]
        repair_case_entry = next(x for x in artifact_contracts if x["artifact_name"] == "repair_case.json")
        assert repair_case_entry["status"] == "missing"
        assert repair_case_entry["blocking"] is True
