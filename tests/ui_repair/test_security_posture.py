import pytest
import asyncio
from httpx import AsyncClient
from datetime import datetime, timezone
from libs.db.models import (
    UIPolicyDrift,
    UISecurityPostureScore,
    UISecurityPostureFinding,
    UIControlStatus,
    UIPostureLevel
)

@pytest.mark.asyncio
async def test_security_posture_scan_flow(client: AsyncClient, db_session):
    """Verifies that a security scan can be triggered and produces a valid score."""
    
    # 1. Trigger Scan
    response = await client.post("/api/v1/ui-repair/security/scan")
    assert response.status_code == 200
    data = response.json()
    
    assert "overall_score" in data
    assert "posture_level" in data
    assert data["posture_level"] in ["SECURE", "RELIABLE", "DEGRADED", "CRITICAL"]

    # 2. Check Findings
    find_resp = await client.get("/api/v1/ui-repair/security/findings")
    assert find_resp.status_code == 200
    findings = find_resp.json()
    assert len(findings) >= 5 # Mandatory controls
    
@pytest.mark.asyncio
async def test_policy_drift_impact_on_posture(client: AsyncClient, db_session):
    """Verifies that detecting a policy drift correctly degrades the security posture score."""
    
    # 1. Create a simulated policy drift
    drift = UIPolicyDrift(
        policy_key="REPAIR_APPROVAL",
        drift_type="UNAUTHORIZED_RELAXATION",
        status="DETECTED",
        drift_level="CRITICAL",
        tenant_key="test-tenant"
    )
    db_session.add(drift)
    await db_session.commit()
    
    # 2. Trigger Scan
    response = await client.post("/api/v1/ui-repair/security/scan?tenant_key=test-tenant")
    assert response.status_code == 200
    data = response.json()
    
    # The score should be degraded due to the drift
    # POL-01-DRIFT will fail (score 0.0), bringing down the average
    assert data["policy_score"] == 0.0
    assert data["overall_score"] < 1.0

@pytest.mark.asyncio
async def test_compliance_certification(client: AsyncClient, db_session):
    """Verifies the generation of a compliance certification record."""
    
    response = await client.post("/api/v1/ui-repair/security/certify?operator_name=TestAgent")
    assert response.status_code == 200
    cert = response.json()
    
    assert cert["cert_id"].startswith("CERT-")
    assert cert["certified_by"] == "TestAgent"
    assert "summary_json" in cert
    assert "findings_json" in cert
