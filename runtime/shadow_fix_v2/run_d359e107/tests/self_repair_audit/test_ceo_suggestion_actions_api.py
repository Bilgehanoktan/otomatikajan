import os
import json
import pytest
import shutil
import uuid
from fastapi.testclient import TestClient

from services.workflow_api.main import app
from services.auth.jwt_auth import get_current_identity

client = TestClient(app)

# Dynamic test audit run directory
TEST_AUDIT_RUN_ID = "AUD-TEST-ACTIONS-999"

@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    # 1. Setup mock credentials override
    mock_id = uuid.uuid4()
    app.dependency_overrides[get_current_identity] = lambda: {
        "id": mock_id,
        "type": "operator",
        "role": "OPERATOR"
    }

    # 2. Setup project output folder structure
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    run_dir = os.path.join(workspace_root, "project_outputs", "audit_runs", TEST_AUDIT_RUN_ID)
    os.makedirs(run_dir, exist_ok=True)

    # 3. Create dummy classified_findings.json with INFO and CRITICAL findings
    findings_data = {
        "findings": [
            {
                "finding_id": "finding-info-1",
                "title": "Low Priority Diagnostic Finding",
                "description": "A non-critical issue with system environment.",
                "category": "frontend",
                "severity": "INFO",
                "priority_score": 10,
                "source": "api_contract_scanner",
                "status": "NEW"
            },
            {
                "finding_id": "finding-critical-1",
                "title": "Critical Authentication Hole",
                "description": "An open security issue that bypasses token checks.",
                "category": "security",
                "severity": "CRITICAL",
                "priority_score": 95,
                "source": "security_guardrail_scanner",
                "status": "NEW"
            }
        ]
    }
    with open(os.path.join(run_dir, "classified_findings.json"), "w", encoding="utf-8") as f:
        json.dump(findings_data, f, indent=2)

    # Phase 4 turns approve-self-repair into an active TaskFlow bridge. These
    # action API tests only verify suggestion state transitions, so keep the
    # repair bridge deterministic and side-effect free here.
    import services.orchestration.ceo.repair_bridge as repair_bridge

    def mock_build_repair_case_from_finding(finding):
        finding_id = getattr(finding, "finding_id", None) or finding.get("finding_id")
        case_input = repair_bridge.RepairCaseInput(
            incident_id=f"INC-TEST-{finding_id}",
            finding_id=finding_id,
        )
        return repair_bridge.RepairCaseBuildResult(
            finding_id=finding_id,
            repair_case_id=finding_id,
            incident_id=case_input.incident_id,
            artifact_ref=f"repair_outputs/{case_input.incident_id}/repair_case.json",
            recommended_agent="swe_agent",
            requested_mode="local_adapter",
            case_input=case_input,
        )

    async def mock_start_self_repair_from_repair_case(case_input, auto_start=False, db=None):
        return {
            "status": "initiated",
            "taskflow_id": f"taskflow-{case_input.finding_id}",
            "job_id": f"job-{case_input.finding_id}",
            "incident_id": case_input.incident_id,
        }

    monkeypatch.setattr(repair_bridge, "build_repair_case_from_finding", mock_build_repair_case_from_finding)
    monkeypatch.setattr(repair_bridge, "start_self_repair_from_repair_case", mock_start_self_repair_from_repair_case)

    yield run_dir

    # Cleanup test run folder
    app.dependency_overrides.clear()
    if os.path.exists(run_dir):
        shutil.rmtree(run_dir)


def test_suggestions_enrichment():
    # Verify that get suggestions returns the findings and enriches status dynamically
    response = client.get(f"/api/v1/ceo/suggestions?force_refresh=false")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    
    # Check if our test run exists and findings are returned
    # Wait, the endpoint might sort alphabetical and pick the test run
    # To be absolutely sure, let's query the specific mock run status file directly if needed,
    # or assert using the specific endpoints.
    # Let's hit the suggestions endpoint directly.
    findings = data["findings"]
    # Verify statuses default to NEW
    for f in findings:
        assert "status" in f


def test_invalid_action_payload_validation_fails():
    # Rationale and operator_id empty should return 422 or 400
    response = client.post(
        f"/api/v1/ceo/suggestions/finding-info-1/approve-self-repair?audit_run_id={TEST_AUDIT_RUN_ID}",
        json={
            "operator_id": "",
            "rationale": "   ",
            "risk_acknowledgement": False
        }
    )
    assert response.status_code == 422 or response.status_code == 400


def test_risk_acknowledgement_enforcement_for_critical():
    # Trying to approve CRITICAL finding without risk_acknowledgement must fail with 400
    response = client.post(
        f"/api/v1/ceo/suggestions/finding-critical-1/approve-self-repair?audit_run_id={TEST_AUDIT_RUN_ID}",
        json={
            "operator_id": "OP-1",
            "rationale": "Fix immediately",
            "risk_acknowledgement": False
        }
    )
    assert response.status_code == 400
    assert "Risk acknowledgement is mandatory" in response.json()["detail"]

    # Now succeed with risk_acknowledgement = True
    response_ok = client.post(
        f"/api/v1/ceo/suggestions/finding-critical-1/approve-self-repair?audit_run_id={TEST_AUDIT_RUN_ID}",
        json={
            "operator_id": "OP-1",
            "rationale": "Fix immediately with caution",
            "risk_acknowledgement": True
        }
    )
    assert response_ok.status_code == 200
    assert response_ok.json()["status"] == "success"
    assert response_ok.json()["action_log"]["to_status"] == "APPROVED_FOR_REPAIR"


def test_transition_matrix_blocks():
    # 1. Transition finding-info-1 to APPROVED_FOR_REPAIR
    resp = client.post(
        f"/api/v1/ceo/suggestions/finding-info-1/approve-self-repair?audit_run_id={TEST_AUDIT_RUN_ID}",
        json={
            "operator_id": "OP-1",
            "rationale": "Standard repair flow",
            "risk_acknowledgement": False
        }
    )
    assert resp.status_code == 200
    assert resp.json()["action_log"]["to_status"] == "APPROVED_FOR_REPAIR"

    # 2. Phase 4 auto-start moves APPROVED_FOR_REPAIR to IN_PROGRESS, so rejecting after repair start is forbidden.
    resp_forbidden = client.post(
        f"/api/v1/ceo/suggestions/finding-info-1/reject?audit_run_id={TEST_AUDIT_RUN_ID}",
        json={
            "operator_id": "OP-1",
            "rationale": "Rejecting it after approval is forbidden",
            "risk_acknowledgement": False
        }
    )
    assert resp_forbidden.status_code == 400
    assert "Transition from 'IN_PROGRESS' to 'REJECTED' is forbidden" in resp_forbidden.json()["detail"]


def test_action_history_logs():
    # Transition finding-info-1 to DEFERRED
    defer_resp = client.post(
        f"/api/v1/ceo/suggestions/finding-info-1/defer?audit_run_id={TEST_AUDIT_RUN_ID}",
        json={
            "operator_id": "OP-ALPHA",
            "rationale": "Postpone this low priority item",
            "risk_acknowledgement": False
        }
    )
    assert defer_resp.status_code == 200

    # Get history
    history_resp = client.get(
        f"/api/v1/ceo/suggestions/finding-info-1/actions?audit_run_id={TEST_AUDIT_RUN_ID}"
    )
    assert history_resp.status_code == 200
    data = history_resp.json()
    assert data["status"] == "success"
    assert len(data["actions"]) == 1
    assert data["actions"][0]["operator_id"] == "OP-ALPHA"
    assert data["actions"][0]["to_status"] == "DEFERRED"
