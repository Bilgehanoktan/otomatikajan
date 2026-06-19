from __future__ import annotations

import json
import os
import shutil
import pytest
from pathlib import Path
from httpx import AsyncClient, ASGITransport

from libs.db.session import get_db
from services.auth import jwt_auth
from services.workflow_api.main import app
from services.repair.taskflow_artifacts import artifact_dir_for_run
from services.repair.github_pr_adapter import prepare_draft_pr

# Workspace Root
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
    incident_id = "INC-API-GATE-99"
    run_id = "RUN-API-GATE-99"
    run_dir = REPAIR_OUTPUTS / incident_id / "taskflow" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    
    # Write mock human_gate_decision.json
    gate_payload = {
        "status": "WAITING_FOR_OPERATOR",
        "incident_id": incident_id,
        "run_id": run_id,
        "risk_score": 0.61,
        "risk_threshold": 0.30,
        "waiting_reason": "Risk 0.61 > threshold 0.30",
        "candidate_ids": ["candidate-001"],
        "required_decision_fields": [
            "operator_id",
            "decision",
            "rationale",
            "selected_candidate_id",
            "risk_acknowledgement",
            "rollback_required"
        ],
        "artifact_refs": {
            "risk_report": "...",
            "patch_candidates": "...",
            "verifier_mesh_result": "...",
            "sandbox_result": "..."
        }
    }
    (run_dir / "human_gate_decision.json").write_text(json.dumps(gate_payload), encoding="utf-8")
    
    # Write mock patch_candidates.json
    candidates_payload = [
        {
            "candidate_id": "candidate-001",
            "policy_status": "allowed",
            "status": "allowed",
            "changed_files": ["src/main.py"]
        }
    ]
    (run_dir / "patch_candidates.json").write_text(json.dumps(candidates_payload), encoding="utf-8")
    
    # Write mock sandbox_result.json
    sandbox_payload = {
        "candidate-001": {"tests_passed": True}
    }
    (run_dir / "sandbox_result.json").write_text(json.dumps(sandbox_payload), encoding="utf-8")
    
    # Write mock verifier_mesh_result.json
    verifier_payload = {
        "verifier_status": "passed",
        "results": []
    }
    (run_dir / "verifier_mesh_result.json").write_text(json.dumps(verifier_payload), encoding="utf-8")
    
    yield incident_id, run_id, run_dir
    
    if REPAIR_OUTPUTS.exists():
        shutil.rmtree(REPAIR_OUTPUTS / incident_id, ignore_errors=True)

@pytest.mark.asyncio
async def test_get_human_gate_returns_waiting_status(api_test_env):
    incident_id, run_id, run_dir = api_test_env
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": "Bearer test-token"},
    ) as ac:
        response = await ac.get(f"/api/v1/repair-lab/runs/{run_id}/human-gate")
        assert response.status_code == 200
        data = response.json()
        assert data["run_id"] == run_id
        assert data["incident_id"] == incident_id
        assert data["human_gate"]["status"] == "WAITING_FOR_OPERATOR"
        assert "HIGH_RISK_GATED" in data["blocking_reasons"]

@pytest.mark.asyncio
async def test_post_human_gate_decision_records_operator_choice(api_test_env):
    incident_id, run_id, run_dir = api_test_env
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": "Bearer test-token"},
    ) as ac:
        payload = {
            "operator_id": "operator-001",
            "decision": "open_draft_pr_only",
            "rationale": "Verifier passed but risk is above automatic apply threshold.",
            "selected_candidate_id": "candidate-001",
            "risk_acknowledgement": True,
            "rollback_required": True,
            "rollback_plan_ref": "repair_outputs/INC-API-GATE-99/rollback_plan.json"
        }
        response = await ac.post(f"/api/v1/repair-lab/runs/{run_id}/human-gate/decision", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["result"]["status"] == "DRAFT_PR_ONLY"

@pytest.mark.asyncio
async def test_post_human_gate_decision_rejects_missing_rationale(api_test_env):
    incident_id, run_id, run_dir = api_test_env
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": "Bearer test-token"},
    ) as ac:
        payload = {
            "operator_id": "operator-001",
            "decision": "open_draft_pr_only",
            "rationale": "   ",
            "selected_candidate_id": "candidate-001",
            "risk_acknowledgement": True,
            "rollback_required": False
        }
        response = await ac.post(f"/api/v1/repair-lab/runs/{run_id}/human-gate/decision", json=payload)
        assert response.status_code == 400
        assert "rationale" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_post_human_gate_decision_rejects_invalid_candidate(api_test_env):
    incident_id, run_id, run_dir = api_test_env
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": "Bearer test-token"},
    ) as ac:
        payload = {
            "operator_id": "operator-001",
            "decision": "open_draft_pr_only",
            "rationale": "Good logic.",
            "selected_candidate_id": "candidate-invalid",
            "risk_acknowledgement": True,
            "rollback_required": False
        }
        response = await ac.post(f"/api/v1/repair-lab/runs/{run_id}/human-gate/decision", json=payload)
        assert response.status_code == 400
        assert "allowed list" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_prepare_draft_pr_blocked_without_human_gate_decision(api_test_env):
    incident_id, run_id, run_dir = api_test_env
    
    # We create a mock context
    from services.repair.repair_models import RepairCase, RepairCandidate, RepairDecision
    
    repair_case = RepairCase(
        incident_id=incident_id,
        summary="API gate test",
        trace_id="...",
        error_type="..."
    )
    
    repair_candidate = RepairCandidate(
        candidate_id="candidate-001",
        patch_path="some/patch.diff",
        changed_files=["main.py"]
    )
    
    risk_decision = RepairDecision(
        status="WAITING_FOR_OPERATOR",
        risk_score=0.61,
        risk_level="HIGH",
        recommended_action="operator_review",
        reason="..."
    )
    
    context = {
        "incident_id": incident_id,
        "run_id": run_id,
        "output_root": REPAIR_OUTPUTS,
        "repair_case": repair_case,
        "repair_candidate": repair_candidate,
        "risk_decision": risk_decision,
        "risk_score": 0.61
    }
    
    # Since status inside human_gate_decision.json is WAITING_FOR_OPERATOR, it must block prepare_draft_pr
    with pytest.raises(ValueError, match="Human Gate Decision artifact is missing|blocks draft PR preparation"):
        prepare_draft_pr(context)
