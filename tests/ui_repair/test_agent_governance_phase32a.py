import uuid
import os
import pytest
import hashlib
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from libs.db.models.ui_repair_models import (
    UIRepairCase,
    UIRepairAttempt,
    UIRepairPRReview,
    UIRepairVerifierRun,
    UIRepairGovernanceApproval,
    UIRepairStatus,
    RepairAttemptStatus,
    PRReviewStatus,
    VerifierStatus,
)
from services.ui_repair.service import UIRepairService
from services.orchestration.agi.security.audit_gate import audit_gate


@pytest.mark.asyncio
async def test_simulate_blocked_requires_test_mode(client: AsyncClient, db_session: AsyncSession):
    # Create a UI Repair case with mandatory project/cluster/tenant keys
    case = UIRepairCase(
        id=uuid.uuid4(),
        route="/workflows",
        title="Test Case",
        status=UIRepairStatus.DETECTED.value,
        tenant_key="test-tenant",
        project_key="test-project",
        cluster_key="test-cluster",
    )
    db_session.add(case)
    await db_session.commit()
    await db_session.refresh(case)

    # 1. Test simulation fails in production (BILGEAPI_UI_REPAIR_TEST_MODE is unset or false)
    if "BILGEAPI_UI_REPAIR_TEST_MODE" in os.environ:
        del os.environ["BILGEAPI_UI_REPAIR_TEST_MODE"]

    response = await client.post(
        f"/api/v1/ui-repair/cases/{case.id}/repair",
        headers={"X-BilgeAPI-Test-Simulate-PR-Review": "BLOCKED"}
    )
    assert response.status_code == 403
    assert "not allowed in production" in response.json()["detail"]

    # 2. Test simulation succeeds when BILGEAPI_UI_REPAIR_TEST_MODE is true
    os.environ["BILGEAPI_UI_REPAIR_TEST_MODE"] = "true"
    response = await client.post(
        f"/api/v1/ui-repair/cases/{case.id}/repair",
        headers={"X-BilgeAPI-Test-Simulate-PR-Review": "BLOCKED"}
    )
    # The endpoint should trigger the background task successfully, returning 200/success
    assert response.status_code in {200, 201}
    assert response.json()["status"] == "success"


@pytest.mark.asyncio
async def test_audit_gate_fail_closed_on_placeholder_or_error(db_session: AsyncSession):
    # Test verify_self_patch on safe file with placeholder model orchestrator (offline)
    # Since we set fail-closed, it should return False
    is_safe = await audit_gate.verify_self_patch("apps/refine_control_plane/src/workflows/page.tsx", "clean code content")
    # It must return False because model orchestrator is offline/placeholder and fail-closed is active
    assert is_safe is False

    # Test static audit denylist patterns (always fail even if LLM is mock-passed)
    is_safe_denylist = await audit_gate.verify_self_patch("libs/db/session.py", "some patch")
    assert is_safe_denylist is False

    is_safe_command = await audit_gate.verify_self_patch("apps/refine_control_plane/src/workflows/page.tsx", "import os; os.remove('file')")
    assert is_safe_command is False


@pytest.mark.asyncio
async def test_apply_patch_requires_passed_review_and_verifier(db_session: AsyncSession):
    # Create case, attempt, and governance approval
    case_id = uuid.uuid4()
    attempt_id = uuid.uuid4()

    case = UIRepairCase(
        id=case_id,
        route="/workflows",
        title="Test Case",
        status=UIRepairStatus.PR_OPENED.value,
        suspected_area="apps/refine_control_plane/src/workflows/page.tsx",
        tenant_key="test-tenant",
        project_key="test-project",
        cluster_key="test-cluster",
    )
    attempt = UIRepairAttempt(
        id=attempt_id,
        case_id=case_id,
        status=RepairAttemptStatus.PR_OPENED.value,
        patch_path="tests/ui_repair/test_patch.patch",
        stagehand_summary_json={"patch_hash": "mock-hash"},
    )
    gov = UIRepairGovernanceApproval(
        case_id=case_id,
        attempt_id=attempt_id,
        status="REQUESTED",
    )
    
    # Create mock patch file
    os.makedirs("tests/ui_repair", exist_ok=True)
    with open("tests/ui_repair/test_patch.patch", "w", encoding="utf-8") as f:
        f.write("mock patch content")
    
    db_session.add(case)
    db_session.add(attempt)
    db_session.add(gov)
    await db_session.commit()

    # 1. Missing review -> fails
    service = UIRepairService(db_session)
    res = await service.apply_patch(str(case_id), str(attempt_id), "operator")
    assert res["status"] == "error"
    assert "PR review not found" in res["message"]

    # 2. Blocked review -> fails
    review = UIRepairPRReview(
        case_id=case_id,
        attempt_id=attempt_id,
        status=PRReviewStatus.BLOCKED.value,
        describe_output_json={"reviewed_patch_hash": "mock-hash"},
    )
    db_session.add(review)
    await db_session.commit()

    res = await service.apply_patch(str(case_id), str(attempt_id), "operator")
    assert res["status"] == "error"
    assert "PR Review status is BLOCKED" in res["message"]

    # 3. Approved review, but missing verifier -> fails
    review.status = PRReviewStatus.PASSED.value
    await db_session.commit()

    res = await service.apply_patch(str(case_id), str(attempt_id), "operator")
    assert res["status"] == "error"
    assert "Verifier run not found" in res["message"]

    # 4. Approved review, failed verifier -> fails
    verifier = UIRepairVerifierRun(
        case_id=case_id,
        attempt_id=attempt_id,
        status=VerifierStatus.FAILED.value,
        result_summary_json={"verified_patch_hash": "mock-hash"},
    )
    db_session.add(verifier)
    await db_session.commit()

    res = await service.apply_patch(str(case_id), str(attempt_id), "operator")
    assert res["status"] == "error"
    assert "Verifier run status is FAILED" in res["message"]


@pytest.mark.asyncio
async def test_apply_patch_requires_hash_match(db_session: AsyncSession, monkeypatch):
    case_id = uuid.uuid4()
    attempt_id = uuid.uuid4()

    case = UIRepairCase(
        id=case_id,
        route="/workflows",
        title="Test Case",
        status=UIRepairStatus.PR_OPENED.value,
        suspected_area="apps/refine_control_plane/src/workflows/page.tsx",
        tenant_key="test-tenant",
        project_key="test-project",
        cluster_key="test-cluster",
    )
    
    # Create mock patch file
    os.makedirs("tests/ui_repair", exist_ok=True)
    patch_path = "tests/ui_repair/test_patch_hash.patch"
    with open(patch_path, "w", encoding="utf-8") as f:
        f.write("mock patch content hash")
    
    attempt = UIRepairAttempt(
        id=attempt_id,
        case_id=case_id,
        status=RepairAttemptStatus.PR_OPENED.value,
        patch_path=patch_path,
    )
    gov = UIRepairGovernanceApproval(
        case_id=case_id,
        attempt_id=attempt_id,
        status="REQUESTED",
    )
    
    correct_hash = hashlib.sha256(b"mock patch content hash").hexdigest()

    review = UIRepairPRReview(
        case_id=case_id,
        attempt_id=attempt_id,
        status=PRReviewStatus.PASSED.value,
        describe_output_json={"reviewed_patch_hash": "different-hash"},
    )
    verifier = UIRepairVerifierRun(
        case_id=case_id,
        attempt_id=attempt_id,
        status=VerifierStatus.PASSED.value,
        result_summary_json={"verified_patch_hash": correct_hash},
    )

    db_session.add(case)
    db_session.add(attempt)
    db_session.add(gov)
    db_session.add(review)
    db_session.add(verifier)
    await db_session.commit()

    # Mock verify_self_patch to return True so we can bypass AuditGate check and test hash matching
    async def mock_verify(*args, **kwargs):
        return True
    monkeypatch.setattr(audit_gate, "verify_self_patch", mock_verify)

    # Apply fails due to hash mismatch between reviewed and applied
    service = UIRepairService(db_session)
    res = await service.apply_patch(str(case_id), str(attempt_id), "operator")
    assert res["status"] == "error"
    assert "Patch identity check failed (hash mismatch)" in res["message"]


@pytest.mark.asyncio
async def test_apply_patch_requires_path_allowlist(db_session: AsyncSession):
    case_id = uuid.uuid4()
    attempt_id = uuid.uuid4()

    # File path is outside allowlist (.env)
    case = UIRepairCase(
        id=case_id,
        route="/workflows",
        title="Test Case",
        status=UIRepairStatus.PR_OPENED.value,
        suspected_area=".env",
        tenant_key="test-tenant",
        project_key="test-project",
        cluster_key="test-cluster",
    )
    attempt = UIRepairAttempt(
        id=attempt_id,
        case_id=case_id,
        status=RepairAttemptStatus.PR_OPENED.value,
        patch_path="tests/ui_repair/test_patch.patch",
    )
    gov = UIRepairGovernanceApproval(
        case_id=case_id,
        attempt_id=attempt_id,
        status="REQUESTED",
    )
    review = UIRepairPRReview(
        case_id=case_id,
        attempt_id=attempt_id,
        status=PRReviewStatus.PASSED.value,
        describe_output_json={"reviewed_patch_hash": "mock-hash"},
    )
    verifier = UIRepairVerifierRun(
        case_id=case_id,
        attempt_id=attempt_id,
        status=VerifierStatus.PASSED.value,
        result_summary_json={"verified_patch_hash": "mock-hash"},
    )

    db_session.add(case)
    db_session.add(attempt)
    db_session.add(gov)
    db_session.add(review)
    db_session.add(verifier)
    await db_session.commit()

    service = UIRepairService(db_session)
    res = await service.apply_patch(str(case_id), str(attempt_id), "operator")
    assert res["status"] == "error"
    assert "outside allowlist" in res["message"]
