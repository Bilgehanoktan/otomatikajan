import pytest
import uuid
from httpx import AsyncClient
from datetime import datetime, timezone
from libs.db.models.ui_repair_models import UISecurityPostureFinding, UIRepairSeverity, RemediationStatus

@pytest.mark.asyncio
async def test_security_remediation_lifecycle(client: AsyncClient, db_session):
    """Verifies the Phase 22 remediation lifecycle for a LOW risk finding."""
    # 1. Create a mock finding
    finding_id = uuid.uuid4()
    finding = UISecurityPostureFinding(
        id=finding_id,
        control_key="DR_01_DASHBOARD_VISIBILITY",
        status="FAILED",
        rationale="Dashboard visibility is missing for some routes.",
        last_check_at=datetime.now(timezone.utc)
    )
    db_session.add(finding)
    await db_session.commit()
    
    # 2. Trigger Remediation Plan
    response = await client.post(f"/api/v1/ui-repair/security/remediation/plan/{finding_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "fix_proposed"
    assert "plan_id" in data
    assert "attempt_id" in data
    
    # 3. Verify Plan in list
    list_response = await client.get("/api/v1/ui-repair/security/remediation/plans")
    assert list_response.status_code == 200
    plans = list_response.json()
    assert any(p["id"] == data["plan_id"] for p in plans)
    
    # 4. Verify Summary
    summary_response = await client.get("/api/v1/ui-repair/security/remediation/summary")
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["total_plans"] >= 1
    assert summary["total_attempts"] >= 1

@pytest.mark.asyncio
async def test_critical_finding_blocks_autofix(client: AsyncClient, db_session):
    """Verifies that CRITICAL findings block auto-fix and require manual review."""
    # 1. Create a CRITICAL finding
    finding_id = uuid.uuid4()
    finding = UISecurityPostureFinding(
        id=finding_id,
        control_key="DR_99_GOVERNANCE_BYPASS",
        status="FAILED",
        rationale="Detected a direct governance bypass in the orchestration layer.",
        last_check_at=datetime.now(timezone.utc)
    )
    db_session.add(finding)
    await db_session.commit()
    
    # 2. Trigger Remediation
    response = await client.post(f"/api/v1/ui-repair/security/remediation/plan/{finding_id}")
    assert response.status_code == 200
    data = response.json()
    
    # 3. Assert it's blocked for manual review
    assert data["status"] == "manual_review_required"
    assert data["severity"] == UIRepairSeverity.CRITICAL.value
    
    # Verify plan status is MANUAL_REQUIRED
    plan_id = data["plan_id"]
    plans_response = await client.get("/api/v1/ui-repair/security/remediation/plans")
    plan = next(p for p in plans_response.json() if p["id"] == plan_id)
    assert plan["status"] == RemediationStatus.MANUAL_REQUIRED.value
