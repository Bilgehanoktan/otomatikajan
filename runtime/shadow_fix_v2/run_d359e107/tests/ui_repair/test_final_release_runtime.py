from datetime import datetime, timezone

import pytest

from libs.db.models.ui_repair_models import (
    UIRepairCase,
    UIRouteHealth,
    UIReleaseReadinessCheck,
    ReleaseStatus,
)
from services.ui_repair.baseline_bootstrap import UIRepairBaselineBootstrapper


@pytest.mark.asyncio
async def test_system_smoke_runner_reflects_real_runtime_state(client, db_session):
    route = UIRouteHealth(
        route="/repair-lab",
        last_status="FAIL",
        last_http_status=500,
        last_checked_at=datetime.now(timezone.utc),
        failure_count=2,
        avg_response_ms=245.0,
        blank_page_detected=True,
        console_error_count=1,
        network_error_count=1,
    )
    db_session.add(route)
    await db_session.commit()

    response = await client.post("/api/v1/ui-repair/final/smoke-test/run")
    assert response.status_code == 200

    payload = {item["module_name"]: item for item in response.json()}
    assert payload["Health Endpoint"]["status"] == "PASSED"
    assert payload["UI Repair Overview"]["status"] == "FAILED"
    assert payload["Knowledge Graph"]["status"] == "FAILED"


@pytest.mark.asyncio
async def test_system_smoke_runner_does_not_fail_for_open_cases_without_route_failures(client, db_session):
    route = UIRouteHealth(
        route="/repair-lab",
        last_status="PASS",
        last_http_status=200,
        last_checked_at=datetime.now(timezone.utc),
        failure_count=0,
        avg_response_ms=120.0,
        blank_page_detected=False,
        console_error_count=0,
        network_error_count=0,
    )
    open_case = UIRepairCase(
        route="/repair-lab",
        status="WAITING_GOVERNANCE",
        severity="HIGH",
        failure_type="NETWORK",
    )
    db_session.add_all([route, open_case])
    await db_session.commit()

    response = await client.post("/api/v1/ui-repair/final/smoke-test/run")
    assert response.status_code == 200

    payload = {item["module_name"]: item for item in response.json()}
    assert payload["UI Repair Overview"]["status"] == "PASSED"

    audit_response = await client.post("/api/v1/ui-repair/final/integration-audit/run")
    assert audit_response.status_code == 200
    audit_payload = audit_response.json()
    assert audit_payload["checked_modules_json"]["UIRepairCore"] == "PASSED"
    assert audit_payload["checked_modules_json"]["ContinuousMonitoring"] == "WARNING"


@pytest.mark.asyncio
async def test_residual_risk_signoff_is_persisted(client, db_session):
    readiness = UIReleaseReadinessCheck(
        check_key="READINESS-PERSIST-1",
        category="Governance",
        status=ReleaseStatus.WARNING,
        score=70.0,
        blockers_json=[],
        warnings_json=["Pending operator acknowledgment"],
        recommendation="Explicitly accept or clear the governance warning.",
    )
    db_session.add(readiness)
    await db_session.commit()

    initial = await client.get("/api/v1/ui-repair/final/residual-risks")
    assert initial.status_code == 200
    risks = initial.json()
    assert risks
    target = risks[0]
    assert target["is_accepted"] is False

    signoff = await client.post(
        f"/api/v1/ui-repair/final/residual-risks/{target['risk_id']}/sign-off",
        json={"operator": "Egemen YAZ"},
    )
    assert signoff.status_code == 200
    assert signoff.json()["accepted_by"] == "Egemen YAZ"
    assert signoff.json()["status"] == "ACCEPTED"

    refreshed = await client.get("/api/v1/ui-repair/final/residual-risks")
    assert refreshed.status_code == 200
    updated_target = next(item for item in refreshed.json() if item["risk_id"] == target["risk_id"])
    assert updated_target["is_accepted"] is True
    assert updated_target["accepted_by"] == "Egemen YAZ"
    assert updated_target["status"] == "ACCEPTED"


@pytest.mark.asyncio
async def test_bootstrap_baseline_clears_core_release_failures(client, db_session):
    bootstrapper = UIRepairBaselineBootstrapper(db_session)
    result = await bootstrapper.ensure_baseline()

    assert result["identities_ready"] is True
    assert result["policies_ready"] is True
    assert result["finops_ready"] is True
    assert result["federation_ready"] is True
    assert result["knowledge_ready"] is True

    smoke_response = await client.post("/api/v1/ui-repair/final/smoke-test/run")
    assert smoke_response.status_code == 200

    smoke_payload = {item["module_name"]: item for item in smoke_response.json()}
    assert smoke_payload["Knowledge Graph"]["status"] == "PASSED"
    assert smoke_payload["Identity Registry"]["status"] == "PASSED"
    assert smoke_payload["Policy Engine"]["status"] == "PASSED"
    assert smoke_payload["FinOps Core"]["status"] == "PASSED"
    assert smoke_payload["Resiliency Mesh"]["status"] == "PASSED"

    audit_response = await client.post("/api/v1/ui-repair/final/integration-audit/run")
    assert audit_response.status_code == 200

    audit_payload = audit_response.json()
    assert audit_payload["checked_modules_json"]["KnowledgeGraph"] == "PASSED"
    assert audit_payload["checked_modules_json"]["FederationMesh"] == "PASSED"
