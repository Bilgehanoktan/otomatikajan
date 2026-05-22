from __future__ import annotations

import json
import os
import shutil
import uuid
from pathlib import Path
import pytest
from httpx import AsyncClient, ASGITransport

from services.workflow_api.main import app
from services.auth.jwt_auth import get_current_identity, require_permission
from services.project_factory.models import (
    ProjectFactoryIntake,
    RequirementGate,
    ApproveDeliveryRequest,
    RevisionRequest,
    RejectCandidateRequest
)
from services.project_factory.artifacts import write_project_factory_artifacts, load_project_factory_artifacts, _resolve_project_dir
from services.project_factory.human_gate_service import (
    approve_candidate_delivery,
    request_candidate_revision,
    reject_candidate_delivery
)

WORKSPACE_ROOT = Path("e:/ai_company_faz12.1").resolve()
TEST_PROJECT_ID = "PF-TEST-HG-222"
TEST_PROJECT_DIR = WORKSPACE_ROOT / "project_outputs" / "project_factory" / TEST_PROJECT_ID

@pytest.fixture(autouse=True)
async def setup_test_environment():
    # 1. Setup authentication overrides
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

    # 2. Setup project outputs base folder
    if TEST_PROJECT_DIR.exists():
        shutil.rmtree(TEST_PROJECT_DIR, ignore_errors=True)
    TEST_PROJECT_DIR.mkdir(parents=True, exist_ok=True)

    # Write initial brief and requirement gate status
    intake = ProjectFactoryIntake(
        project_id=TEST_PROJECT_ID,
        source_suggestion_id="sug-hg-222",
        audit_run_id="AUD-HG-222",
        title="Test Human Gate Project",
        problem_statement="Testing operator approval gating",
        recommended_action="Execute human-gate approvals",
        affected_files=["app/main.py"],
        status="HUMAN_GATE_WAITING"
    )
    gate = RequirementGate(
        gate="Requirement Approval Gate",
        status="HUMAN_GATE_WAITING",
        allowed_actions=["approve_scope", "request_revision", "reject"]
    )
    write_project_factory_artifacts(intake, gate, str(WORKSPACE_ROOT))

    # Scaffold mock files needed for review checks
    manifest_data = {
        "project_id": TEST_PROJECT_ID,
        "candidate_id": "CAND-PF-222",
        "status": "CANDIDATE_READY",
        "files": [{"path": "app/main.py", "checksum": "abc123main"}]
    }
    with open(TEST_PROJECT_DIR / "candidate_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest_data, f)

    with open(TEST_PROJECT_DIR / "verification_report.json", "w", encoding="utf-8") as f:
        json.dump({"status": "PASSED"}, f)

    with open(TEST_PROJECT_DIR / "quality_scorecard.json", "w", encoding="utf-8") as f:
        json.dump({"score": 100}, f)

    # Create candidate package directory
    cand_dir = TEST_PROJECT_DIR / "candidate_package"
    cand_dir.mkdir(parents=True, exist_ok=True)
    os.makedirs(cand_dir / "app", exist_ok=True)
    with open(cand_dir / "app" / "main.py", "w", encoding="utf-8") as f:
        f.write("print('hello')\n")

    yield

    # Cleanup
    app.dependency_overrides.clear()
    if TEST_PROJECT_DIR.exists():
        shutil.rmtree(TEST_PROJECT_DIR, ignore_errors=True)


def test_approve_delivery_unacknowledged_fails():
    """
    Verifies that approving delivery without acknowledging risks fails with ValueError.
    """
    # Create low-risk risk assessment
    with open(TEST_PROJECT_DIR / "risk_assessment.json", "w", encoding="utf-8") as f:
        json.dump({"risk_score": 20, "blocking_risks": [], "warnings": []}, f)

    req = ApproveDeliveryRequest(
        operator_id="OP-HG-1",
        rationale="Looks good!",
        risk_acknowledgement=False
    )
    with pytest.raises(ValueError, match="acknowledge risks"):
        approve_candidate_delivery(TEST_PROJECT_ID, req, str(WORKSPACE_ROOT))


def test_approve_delivery_high_risk_blocked():
    """
    Verifies that high risk score blocks delivery approval.
    """
    # Create high-risk risk assessment
    with open(TEST_PROJECT_DIR / "risk_assessment.json", "w", encoding="utf-8") as f:
        json.dump({"risk_score": 75, "blocking_risks": ["Dangerous keywords found"], "warnings": []}, f)

    req = ApproveDeliveryRequest(
        operator_id="OP-HG-1",
        rationale="Looks good!",
        risk_acknowledgement=True
    )
    with pytest.raises(ValueError, match="blocked due to high risk"):
        approve_candidate_delivery(TEST_PROJECT_ID, req, str(WORKSPACE_ROOT))


def test_approve_delivery_success():
    """
    Verifies that valid operator approval generates delivery package, transitions state.
    """
    # Create low-risk risk assessment
    with open(TEST_PROJECT_DIR / "risk_assessment.json", "w", encoding="utf-8") as f:
        json.dump({"risk_score": 10, "blocking_risks": [], "warnings": []}, f)

    req = ApproveDeliveryRequest(
        operator_id="OP-HG-1",
        rationale="Excellent template implementation.",
        risk_acknowledgement=True
    )
    res = approve_candidate_delivery(TEST_PROJECT_ID, req, str(WORKSPACE_ROOT))
    assert res["status"] == "success"
    assert res["gate_status"] == "DELIVERY_PACKAGE_READY"
    assert res["delivery_manifest"]["production_apply_allowed"] is False


@pytest.mark.asyncio
async def test_human_gate_endpoints():
    """
    Verifies manual decision routes and delivery logs stream endpoint.
    """
    # 1. Create low-risk risk assessment
    with open(TEST_PROJECT_DIR / "risk_assessment.json", "w", encoding="utf-8") as f:
        json.dump({"risk_score": 10, "blocking_risks": [], "warnings": []}, f)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Request Revision Endpoint
        rev_resp = await ac.post(
            f"/api/v1/project-factory/{TEST_PROJECT_ID}/human-gate/request-revision",
            json={
                "operator_id": "OP-HG-1",
                "rationale": "Missing comments",
                "revision_notes": "Please document key functions."
            }
        )
        assert rev_resp.status_code == 200
        assert rev_resp.json()["gate_status"] == "REVISION_REQUESTED"

        # Change state back manually so we can test reject/approve endpoint
        intake, gate = load_project_factory_artifacts(TEST_PROJECT_ID, str(WORKSPACE_ROOT))
        intake.status = "HUMAN_GATE_WAITING"
        gate.status = "HUMAN_GATE_WAITING"
        write_project_factory_artifacts(intake, gate, str(WORKSPACE_ROOT))

        # Reject Endpoint
        rej_resp = await ac.post(
            f"/api/v1/project-factory/{TEST_PROJECT_ID}/human-gate/reject",
            json={
                "operator_id": "OP-HG-1",
                "rationale": "Totally out of scope."
            }
        )
        assert rej_resp.status_code == 200
        assert rej_resp.json()["gate_status"] == "REJECTED"

        # Reset state back again
        intake.status = "HUMAN_GATE_WAITING"
        gate.status = "HUMAN_GATE_WAITING"
        write_project_factory_artifacts(intake, gate, str(WORKSPACE_ROOT))

        # Approve Endpoint
        app_resp = await ac.post(
            f"/api/v1/project-factory/{TEST_PROJECT_ID}/human-gate/approve-delivery",
            json={
                "operator_id": "OP-HG-1",
                "rationale": "Perfect implementation.",
                "risk_acknowledgement": True
            }
        )
        assert app_resp.status_code == 200
        assert app_resp.json()["gate_status"] == "DELIVERY_PACKAGE_READY"

        # Retrieve Decisions Logs (append-only)
        logs_resp = await ac.get(f"/api/v1/project-factory/{TEST_PROJECT_ID}/delivery/logs")
        assert logs_resp.status_code == 200
        logs = logs_resp.json()["logs"]
        assert len(logs) == 3
        assert logs[0]["action"] == "REQUEST_REVISION"
        assert logs[1]["action"] == "REJECT"
        assert logs[2]["action"] == "APPROVE_DELIVERY"
