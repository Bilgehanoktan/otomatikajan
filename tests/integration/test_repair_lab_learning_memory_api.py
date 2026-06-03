from __future__ import annotations

import json
import shutil
import pytest
from pathlib import Path
from httpx import AsyncClient, ASGITransport

from services.workflow_api.main import app

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
REPAIR_OUTPUTS = WORKSPACE_ROOT / "repair_outputs"

@pytest.fixture
def setup_mock_artifacts():
    run_id = "test-run-phase8"
    incident_id = "INC-TEST-PHASE8"
    
    run_dir = REPAIR_OUTPUTS / incident_id / "taskflow" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    
    score_payload = {
        "incident_id": incident_id,
        "run_id": run_id,
        "candidate_scores": [
            {
                "candidate_id": "cand-001",
                "agent_key": "expert_agent",
                "strategy": "conservative",
                "base_score": 0.70,
                "historical_success_score": 0.85,
                "memory_adjustment": 0.05,
                "final_score": 0.75,
                "explanation": "Expert agent memory adjustment"
            }
        ]
    }
    (run_dir / "candidate_memory_score.json").write_text(json.dumps(score_payload), encoding="utf-8")
    
    profile_dir = REPAIR_OUTPUTS / "learning_memory" / "profiles"
    profile_dir.mkdir(parents=True, exist_ok=True)
    profile_payload = {
        "agent_key": "expert_agent",
        "strategy": "conservative",
        "total_attempts": 5,
        "successful_attempts": 4,
        "failed_attempts": 1,
        "historical_success_score": 0.80
    }
    (profile_dir / "expert_agent_conservative.json").write_text(json.dumps(profile_payload), encoding="utf-8")
    
    yield {
        "run_id": run_id,
        "incident_id": incident_id,
        "profile_dir": profile_dir,
        "run_dir": run_dir
    }
    
    shutil.rmtree(REPAIR_OUTPUTS / incident_id, ignore_errors=True)
    if (profile_dir / "expert_agent_conservative.json").exists():
        (profile_dir / "expert_agent_conservative.json").unlink()


@pytest.mark.asyncio
async def test_get_run_memory_score_success(setup_mock_artifacts):
    run_id = setup_mock_artifacts["run_id"]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(f"/api/v1/repair-lab/runs/{run_id}/memory-score")
        assert response.status_code == 200
        data = response.json()
        assert data["run_id"] == run_id
        assert len(data["candidate_scores"]) == 1
        assert data["candidate_scores"][0]["agent_key"] == "expert_agent"


@pytest.mark.asyncio
async def test_get_run_memory_score_not_found():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/repair-lab/runs/nonexistent-run-id/memory-score")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_run_memory_score_path_traversal():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Starlette normalizes raw /.. so we use the URL-encoded backslash sequence
        response = await ac.get("/api/v1/repair-lab/runs/..%5Chack/memory-score")
        assert response.status_code == 400
        assert "Path traversal detected" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_learning_memory_profile_success(setup_mock_artifacts):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/repair-lab/learning-memory/profiles/expert_agent/conservative")
        assert response.status_code == 200
        data = response.json()
        assert data["agent_key"] == "expert_agent"
        assert data["strategy"] == "conservative"
        assert data["historical_success_score"] == 0.80


@pytest.mark.asyncio
async def test_get_learning_memory_profile_not_found():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/repair-lab/learning-memory/profiles/no_agent/no_strategy")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_learning_memory_profile_path_traversal():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response1 = await ac.get("/api/v1/repair-lab/learning-memory/profiles/..%5Chack/conservative")
        assert response1.status_code == 400
        assert "Path traversal detected" in response1.json()["detail"]
        
        response2 = await ac.get("/api/v1/repair-lab/learning-memory/profiles/expert_agent/..%5Chack")
        assert response2.status_code == 400
        assert "Path traversal detected" in response2.json()["detail"]
