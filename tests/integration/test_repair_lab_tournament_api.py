from __future__ import annotations

import json
import shutil
import pytest
from pathlib import Path
from httpx import AsyncClient, ASGITransport

from bilgeapi.libs.db.session import get_db
from services.auth import jwt_auth
from services.workflow_api.main import app

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
REPAIR_OUTPUTS = WORKSPACE_ROOT / "repair_outputs"


class _ScalarNoneResult:
    def scalar_one_or_none(self):
        return None


class _FakeDb:
    async def execute(self, *args, **kwargs):
        return _ScalarNoneResult()


@pytest.fixture(autouse=True)
def _authorized_operator(monkeypatch):
    async def _identity_from_token(db, token):
        return {
            "id": "operator-test",
            "type": "operator",
            "role": "OPERATOR",
            "email": "operator@test.local",
            "name": "Repair Lab Operator",
        }

    async def _db():
        yield _FakeDb()

    app.dependency_overrides[get_db] = _db
    monkeypatch.setattr(jwt_auth.auth_service, "get_identity_from_token", _identity_from_token)
    yield
    app.dependency_overrides.clear()

@pytest.fixture
def setup_mock_artifacts():
    run_id = "test-run-phase9"
    incident_id = "INC-TEST-PHASE9"
    
    run_dir = REPAIR_OUTPUTS / incident_id / "taskflow" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    
    candidates = [
        {
            "candidate_id": "cand-001",
            "candidate_source": "swe_agent",
            "agent_key": "swe_agent",
            "strategy": "conservative",
            "diff_ref": "sandbox/patch.diff",
            "diff": "--- a/page.tsx\n+++ b/page.tsx\n",
            "policy_status": "approved",
            "sandbox_status": "passed",
            "verifier_status": "passed",
            "base_score": 0.70
        }
    ]
    (run_dir / "patch_candidates.json").write_text(json.dumps(candidates), encoding="utf-8")
    
    tournament_payload = {
        "incident_id": incident_id,
        "run_id": run_id,
        "status": "completed",
        "selected_candidate_id": "cand-001",
        "requires_human_gate": True,
        "candidates": [
            {
                "candidate_id": "cand-001",
                "eligible": True,
                "final_score": 0.85,
                "disqualification_reasons": []
            }
        ]
    }
    (run_dir / "tournament_result.json").write_text(json.dumps(tournament_payload), encoding="utf-8")
    
    yield {
        "run_id": run_id,
        "incident_id": incident_id,
        "run_dir": run_dir
    }
    
    shutil.rmtree(REPAIR_OUTPUTS / incident_id, ignore_errors=True)


@pytest.mark.asyncio
async def test_get_run_tournament_success(setup_mock_artifacts):
    run_id = setup_mock_artifacts["run_id"]
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": "Bearer test-token"}
    ) as ac:
        response = await ac.get(f"/api/v1/repair-lab/runs/{run_id}/tournament")
        assert response.status_code == 200
        data = response.json()
        assert data["run_id"] == run_id
        assert data["selected_candidate_id"] == "cand-001"
        assert len(data["candidates"]) == 1
        assert data["candidates"][0]["candidate_id"] == "cand-001"


@pytest.mark.asyncio
async def test_get_run_tournament_not_found():
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": "Bearer test-token"}
    ) as ac:
        response = await ac.get("/api/v1/repair-lab/runs/nonexistent-run-id/tournament")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_run_tournament_path_traversal():
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": "Bearer test-token"}
    ) as ac:
        response = await ac.get("/api/v1/repair-lab/runs/..%5Chack/tournament")
        assert response.status_code == 400
        assert "Path traversal detected" in response.json()["detail"]


@pytest.mark.asyncio
async def test_post_recompute_tournament_success(setup_mock_artifacts):
    run_id = setup_mock_artifacts["run_id"]
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": "Bearer test-token"}
    ) as ac:
        response = await ac.post(f"/api/v1/repair-lab/runs/{run_id}/tournament/recompute")
        assert response.status_code == 200
        data = response.json()
        assert data["run_id"] == run_id
        assert data["status"] == "completed"
        assert data["selected_candidate_id"] == "cand-001"


@pytest.mark.asyncio
async def test_post_recompute_tournament_not_found():
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": "Bearer test-token"}
    ) as ac:
        response = await ac.post("/api/v1/repair-lab/runs/nonexistent-run-id/tournament/recompute")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_post_recompute_tournament_path_traversal():
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": "Bearer test-token"}
    ) as ac:
        response = await ac.post("/api/v1/repair-lab/runs/..%5Chack/tournament/recompute")
        assert response.status_code == 400
        assert "Path traversal detected" in response.json()["detail"]
