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
from services.project_factory.models import ProjectFactoryIntake, RequirementGate
from services.project_factory.artifacts import write_project_factory_artifacts, _resolve_project_dir
from services.project_factory.candidate_review import run_candidate_review, load_candidate_review

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
TEST_PROJECT_ID = "PF-TEST-REVIEW-111"
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
        source_suggestion_id="sug-review-111",
        audit_run_id="AUD-REVIEW-111",
        title="Test Review Project Factory",
        problem_statement="Review and scoring testing",
        recommended_action="Validate review engine",
        affected_files=["app/main.py"],
        status="CANDIDATE_READY"
    )
    gate = RequirementGate(
        gate="Requirement Approval Gate",
        status="CANDIDATE_READY",
        allowed_actions=["approve_scope", "request_revision", "reject"]
    )
    write_project_factory_artifacts(intake, gate, str(WORKSPACE_ROOT))

    yield

    # Cleanup
    app.dependency_overrides.clear()
    if TEST_PROJECT_DIR.exists():
        shutil.rmtree(TEST_PROJECT_DIR, ignore_errors=True)


def test_candidate_review_missing_manifest_fails():
    """
    Verifies that running the review raises FileNotFoundError if candidate manifest doesn't exist.
    """
    with pytest.raises(FileNotFoundError):
        run_candidate_review(TEST_PROJECT_ID, str(WORKSPACE_ROOT))


def test_candidate_review_scoring_and_assessment():
    """
    Verifies scoring metrics, quality scorecard, risk assessor outputs, and transition states.
    """
    # 1. Create candidate_manifest.json
    manifest_data = {
        "project_id": TEST_PROJECT_ID,
        "candidate_id": "CAND-PF-111",
        "status": "CANDIDATE_READY",
        "files": [
            {"path": "app/main.py", "checksum": "abc123main"}
        ],
        "tests": {
            "status": "PASSED",
            "commands": ["pytest"]
        },
        "known_limitations": []
    }
    with open(TEST_PROJECT_DIR / "candidate_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest_data, f)

    # 2. Create verification_report.json
    report_data = {
        "status": "PASSED",
        "duration": 1.23,
        "checks": []
    }
    with open(TEST_PROJECT_DIR / "verification_report.json", "w", encoding="utf-8") as f:
        json.dump(report_data, f)

    # 3. Create candidate_package and a candidate file app/main.py (Clean code)
    cand_dir = TEST_PROJECT_DIR / "candidate_package"
    cand_dir.mkdir(parents=True, exist_ok=True)
    os.makedirs(cand_dir / "app", exist_ok=True)
    with open(cand_dir / "app" / "main.py", "w", encoding="utf-8") as f:
        f.write("def hello():\n    return 'world'\n")

    # Run review
    review = run_candidate_review(TEST_PROJECT_ID, str(WORKSPACE_ROOT))
    assert review.project_id == TEST_PROJECT_ID
    assert review.quality_score == 100
    assert review.risk_score == 22 # Default baseline low risk
    assert review.recommended_decision == "APPROVE_DELIVERY"
    assert review.status == "CANDIDATE_REVIEWED"

    # Verify transition state on disk
    loaded_review = load_candidate_review(TEST_PROJECT_ID, str(WORKSPACE_ROOT))
    assert loaded_review is not None
    assert loaded_review["quality_score"] == 100

    # Ensure quality_scorecard.json and risk_assessment.json exist on disk
    assert (TEST_PROJECT_DIR / "quality_scorecard.json").exists()
    assert (TEST_PROJECT_DIR / "risk_assessment.json").exists()


def test_candidate_review_high_risk_rejection():
    """
    Verifies that files containing hazardous content like os.system score higher risk, transitioning recommended decision to REJECT or REQUEST_REVISION.
    """
    # 1. Create candidate_manifest.json
    manifest_data = {
        "project_id": TEST_PROJECT_ID,
        "candidate_id": "CAND-PF-111",
        "status": "CANDIDATE_READY",
        "files": [
            {"path": "app/main.py", "checksum": "abc123main"}
        ],
        "tests": {
            "status": "PASSED",
            "commands": ["pytest"]
        },
        "known_limitations": ["Requires manual dependency installs"]
    }
    with open(TEST_PROJECT_DIR / "candidate_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest_data, f)

    # 2. Create verification_report.json
    report_data = {
        "status": "PASSED",
        "duration": 1.23,
        "checks": []
    }
    with open(TEST_PROJECT_DIR / "verification_report.json", "w", encoding="utf-8") as f:
        json.dump(report_data, f)

    # 3. Create candidate_package and app/main.py containing os.system (hazardous)
    cand_dir = TEST_PROJECT_DIR / "candidate_package"
    cand_dir.mkdir(parents=True, exist_ok=True)
    os.makedirs(cand_dir / "app", exist_ok=True)
    with open(cand_dir / "app" / "main.py", "w", encoding="utf-8") as f:
        f.write("import os\nos.system('rm -rf /')\neval('1+1')\n")

    # Run review
    review = run_candidate_review(TEST_PROJECT_ID, str(WORKSPACE_ROOT))
    assert review.quality_score == 86 # 100 - 14 due to known limitations
    # 25 points for os.system + 25 points for eval( = 50 risk score
    assert review.risk_score == 50
    # Between 40 and 70 points transitions to REQUEST_REVISION
    assert review.recommended_decision == "REQUEST_REVISION"


@pytest.mark.asyncio
async def test_candidate_review_rest_endpoints():
    """
    Verifies candidate review trigger (POST) and retrieval (GET) REST endpoints.
    """
    # Create required manifests
    manifest_data = {
        "project_id": TEST_PROJECT_ID,
        "candidate_id": "CAND-PF-111",
        "status": "CANDIDATE_READY",
        "files": [
            {"path": "app/main.py", "checksum": "abc123main"}
        ]
    }
    with open(TEST_PROJECT_DIR / "candidate_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest_data, f)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Trigger review via endpoint
        response = await ac.post(f"/api/v1/project-factory/{TEST_PROJECT_ID}/candidate/review")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["candidate_review"]["status"] == "CANDIDATE_REVIEWED"

        # Fetch review details via endpoint
        get_response = await ac.get(f"/api/v1/project-factory/{TEST_PROJECT_ID}/candidate/review")
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["status"] == "success"
        assert get_data["candidate_review"]["status"] == "CANDIDATE_REVIEWED"
        assert "quality_scorecard" in get_data
        assert "risk_assessment" in get_data
