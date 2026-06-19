from __future__ import annotations

import json
import shutil
import pytest
from pathlib import Path
from httpx import AsyncClient, ASGITransport

from libs.db.session import get_db
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
def api_test_env():
    incident_id = "INC-API-DRAFT-88"
    run_id = "RUN-API-DRAFT-88"
    run_dir = REPAIR_OUTPUTS / incident_id / "taskflow" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    
    # Write mock human_gate_decision.json
    gate_payload = {
        "status": "APPROVED",
        "selected_candidate_id": "candidate-001",
        "decision": "approve_and_apply",
        "rationale": "Matches strict verification filters.",
        "risk_score": 0.15,
        "risk_level": "LOW"
    }
    (run_dir / "human_gate_decision.json").write_text(json.dumps(gate_payload), encoding="utf-8")
    
    # Write mock pr_review.json
    review_payload = {
        "status": "completed",
        "review_passed": True,
        "confidence": 0.95,
        "findings": [],
        "blocking_comments": [],
        "suggested_improvements": []
    }
    (run_dir / "pr_review.json").write_text(json.dumps(review_payload), encoding="utf-8")
    
    # Write mock patch_candidates.json
    candidates_payload = [
        {
            "candidate_id": "candidate-001",
            "changed_files": ["src/main.py"]
        }
    ]
    (run_dir / "patch_candidates.json").write_text(json.dumps(candidates_payload), encoding="utf-8")
    
    # Write mock sandbox_result.json
    sandbox_payload = {
        "tests_passed": True,
        "status": "passed"
    }
    (run_dir / "sandbox_result.json").write_text(json.dumps(sandbox_payload), encoding="utf-8")
    
    # Write mock verifier_mesh_result.json
    verifier_payload = {
        "status": "passed",
        "verifier_passed": True
    }
    (run_dir / "verifier_mesh_result.json").write_text(json.dumps(verifier_payload), encoding="utf-8")
    
    # Write taskflow_run.json
    (run_dir / "taskflow_run.json").write_text(
        json.dumps({"run_id": run_id, "status": "WAITING_HUMAN"}), encoding="utf-8"
    )
    
    yield incident_id, run_id, run_dir
    
    if REPAIR_OUTPUTS.exists():
        shutil.rmtree(REPAIR_OUTPUTS / incident_id, ignore_errors=True)

@pytest.mark.asyncio
async def test_get_pr_review_endpoint(api_test_env):
    incident_id, run_id, run_dir = api_test_env
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": "Bearer test-token"},
    ) as ac:
        response = await ac.get(f"/api/v1/repair-lab/runs/{run_id}/pr-review")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["review_passed"] is True

@pytest.mark.asyncio
async def test_post_prepare_draft_pr_endpoint(api_test_env):
    incident_id, run_id, run_dir = api_test_env
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": "Bearer test-token"},
    ) as ac:
        # Trigger preparation manually
        response = await ac.post(
            f"/api/v1/repair-lab/runs/{run_id}/draft-pr/prepare",
            json={"operator_acknowledged_blocking_comments": False}
        )
        assert response.status_code == 200
        res_data = response.json()
        assert res_data["status"] == "ok"
        assert res_data["result"]["draft_pr"]["status"] == "DRAFT_PR_READY"
        
        # Verify metadata endpoint
        response = await ac.get(f"/api/v1/repair-lab/runs/{run_id}/draft-pr")
        assert response.status_code == 200
        metadata = response.json()
        assert metadata["status"] == "DRAFT_PR_READY"
        assert metadata["incident_id"] == incident_id
        assert metadata["selected_candidate_id"] == "candidate-001"
        assert metadata["risk_score"] == 0.15
        
        # Verify taskflow_run.json status in run_dir was updated to PR_DRAFTED
        run_json = json.loads((run_dir / "taskflow_run.json").read_text(encoding="utf-8"))
        assert run_json["status"] == "PR_DRAFTED"

@pytest.mark.asyncio
async def test_get_endpoints_not_found():
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": "Bearer test-token"},
    ) as ac:
        # PR review not found
        response = await ac.get("/api/v1/repair-lab/runs/RUN-NON-EXISTENT/pr-review")
        assert response.status_code == 404
        
        # Draft PR not found
        response = await ac.get("/api/v1/repair-lab/runs/RUN-NON-EXISTENT/draft-pr")
        assert response.status_code == 404
