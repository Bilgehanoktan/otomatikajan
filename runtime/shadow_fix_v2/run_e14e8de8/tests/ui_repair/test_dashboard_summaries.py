import uuid
from datetime import datetime, timezone

import pytest

from libs.db.models.ui_repair_models import (
    UIRepairProjectProfile,
    UIProjectHealthSnapshot,
    UIRouteHealth,
    UISmokeRun,
    UIRepairCase,
    UITenantProfile,
    UIClusterProfile,
    UIProviderHealth,
    UIExternalTool,
    UIThirdPartyRiskAssessment,
    UIGuardrailTuningProposal,
    UIDefensivePattern,
    UIDefenseOptimizationReport,
    GuardrailTuningStatus,
    ProviderStatus,
    UIAutoPatchExecution,
    UIVerificationRunV2,
    AutoPatchExecutionStatus,
    UIFinalIntegrationAudit,
    UIReleaseReadinessCheck,
    ReleaseStatus,
)


@pytest.mark.asyncio
async def test_dashboard_summary_endpoints_return_real_data(client, db_session):
    project = UIRepairProjectProfile(
        project_key="CONTROL_PLANE",
        project_name="Control Plane",
        environment="PRODUCTION",
        status="ACTIVE",
    )
    snapshot = UIProjectHealthSnapshot(
        project_key="CONTROL_PLANE",
        health_score=92.5,
        monitoring_status="ACTIVE",
        open_cases=2,
        critical_cases=1,
        governance_waiting=1,
        active_repairs=1,
        sla_status="COMPLIANT",
        slo_status="HEALTHY",
    )
    tenant = UITenantProfile(tenant_key="ACME", tenant_name="Acme")
    cluster = UIClusterProfile(
        cluster_key="eu-west-1",
        cluster_name="EU West",
        region="eu-west-1",
        environment="production",
        status="HEALTHY",
    )
    provider = UIProviderHealth(
        provider="OpenAI",
        status=ProviderStatus.DEGRADED,
        latency_ms=240,
        error_rate=0.12,
        health_score=0.64,
        cost_spike_detected=True,
        created_at=datetime.now(timezone.utc),
    )
    tool = UIExternalTool(
        tool_key="browser",
        tool_name="Browser",
        tool_type="BROWSER_AUTOMATION",
        provider="OpenAI",
        enabled=True,
        risk_level="MEDIUM",
    )
    risk = UIThirdPartyRiskAssessment(
        provider="OpenAI",
        tool_key="browser",
        risk_score=52.0,
        risk_level="HIGH",
        findings_json=["Provider degraded"],
        recommendation="Enable approval",
    )
    proposal = UIGuardrailTuningProposal(
        proposal_key="PROP-1",
        source_type="POSTURE",
        affected_guardrail="browser",
        affected_policy_key="BROWSER_SANDBOX",
        current_config_json={"threshold": 0.4},
        proposed_config_json={"threshold": 0.6},
        reason="Reduce exposure",
        expected_security_gain=0.2,
        expected_false_positive_impact=0.0,
        expected_false_negative_impact=-0.1,
        risk_level="LOW",
        status=GuardrailTuningStatus.GOVERNANCE_REQUESTED,
    )
    pattern = UIDefensivePattern(
        pattern_key="PATTERN-1",
        pattern_type="SANDBOX",
        affected_domain="TOOL_GOVERNANCE",
        description="Restrict browser writes",
        detection_rule_json={"mode": "strict"},
        mitigation_rule_json={"approval": "required"},
        confidence=0.91,
        status="ACTIVE",
    )
    report = UIDefenseOptimizationReport(
        report_name="Daily report",
        period_start=datetime.now(timezone.utc),
        period_end=datetime.now(timezone.utc),
        total_proposals=1,
        approved_proposals=0,
        rejected_proposals=0,
        security_score_before=72.0,
        security_score_after=78.0,
        false_allow_delta=-2,
        false_block_delta=0,
        executive_summary="Security improved.",
        generated_at=datetime.now(timezone.utc),
    )

    db_session.add_all([project, snapshot, tenant, cluster, provider, tool, risk, proposal, pattern, report])
    await db_session.commit()

    health_resp = await client.get("/api/v1/ui-repair/projects/health-matrix")
    assert health_resp.status_code == 200
    assert health_resp.json()[0]["project_name"] == "Control Plane"
    assert health_resp.json()[0]["health_score"] == 92.5

    defense_resp = await client.get("/api/v1/ui-repair/security/defense/overview")
    assert defense_resp.status_code == 200
    assert defense_resp.json()["total_proposals"] >= 1
    assert defense_resp.json()["patterns_synthesized"] >= 1

    tool_resp = await client.get("/api/v1/ui-repair/tools/risk/overview")
    assert tool_resp.status_code == 200
    assert tool_resp.json()["provider_count"] == 1
    assert tool_resp.json()["highest_risk_level"] == "HIGH"

    federation_resp = await client.get("/api/v1/ui-repair/federation/overview")
    assert federation_resp.status_code == 200
    assert federation_resp.json()["total_tenants"] == 1
    assert federation_resp.json()["active_clusters"] == 1


@pytest.mark.asyncio
async def test_ui_repair_dashboard_summary_uses_fast_operational_snapshot(client, db_session):
    now = datetime.now(timezone.utc)
    failed_route = UIRouteHealth(
        route="/repair-lab",
        last_status="FAIL",
        last_http_status=500,
        last_checked_at=now,
    )
    passing_route = UIRouteHealth(
        route="/system-health",
        last_status="PASS",
        last_http_status=200,
        last_checked_at=now,
    )
    critical_case = UIRepairCase(
        route="/repair-lab",
        status="DETECTED",
        severity="CRITICAL",
        failure_type="BLANK_PAGE",
    )
    active_case = UIRepairCase(
        route="/repair-lab",
        status="WAITING_GOVERNANCE",
        severity="HIGH",
        failure_type="NETWORK",
    )
    smoke = UISmokeRun(
        status="COMPLETED",
        total_routes=2,
        passed_routes=1,
        failed_routes=1,
        started_at=now,
        finished_at=now,
    )

    db_session.add_all([failed_route, passing_route, critical_case, active_case, smoke])
    await db_session.commit()

    summary_resp = await client.get("/api/v1/ui-repair/dashboard/summary")
    assert summary_resp.status_code == 200
    summary = summary_resp.json()
    assert summary["failing_routes"] == 1
    assert summary["open_cases"] == 2
    assert summary["critical_cases"] == 1
    assert summary["last_smoke_status"] == "COMPLETED"

    overview_resp = await client.get("/api/v1/ui-repair/overview")
    assert overview_resp.status_code == 200
    overview = overview_resp.json()
    assert overview["failing_routes"] == 1
    assert overview["open_cases"] == 2
    assert overview["critical_cases"] == 1
    assert any(item["type"] == "BLANK_PAGE" for item in overview["top_failure_types"])


@pytest.mark.asyncio
async def test_final_release_endpoints_are_data_driven(client, db_session):
    execution = UIAutoPatchExecution(
        execution_key="EXEC-READY",
        source_type="MANUAL_TRIGGER",
        source_id=uuid.uuid4(),
        status=AutoPatchExecutionStatus.GOVERNANCE_REQUESTED,
        risk_level="MEDIUM",
    )
    audit = UIFinalIntegrationAudit(
        audit_key="AUDIT-READY",
        status=ReleaseStatus.WARNING,
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        checked_modules_json={"UIRepairCore": "PASSED", "ToolGovernance": "WARNING"},
        failed_modules_json=[],
        warnings_json=["ToolGovernance"],
        summary_json={"total_modules": 2, "passed": 1, "failed": 0, "warnings": 1},
        evidence_hash="SHA256:test",
    )
    readiness = UIReleaseReadinessCheck(
        check_key="READINESS-1",
        category="Governance",
        status=ReleaseStatus.WARNING,
        score=72.0,
        blockers_json=["Pending governance action"],
        warnings_json=["Operator approval waiting"],
        recommendation="Do not lock release yet.",
    )

    db_session.add_all([execution, audit, readiness])
    await db_session.commit()

    matrix_resp = await client.get("/api/v1/ui-repair/final/phase-completion-matrix")
    assert matrix_resp.status_code == 200
    matrix = matrix_resp.json()
    phase_27 = next(item for item in matrix if item["phase_id"] == 27)
    phase_30 = next(item for item in matrix if item["phase_id"] == 30)
    assert phase_27["status"] in {"RUNNING", "WARNING", "PASSED"}
    assert phase_30["warnings_count"] >= 1

    residual_resp = await client.get("/api/v1/ui-repair/final/residual-risks")
    assert residual_resp.status_code == 200
    risks = residual_resp.json()
    assert any(risk["module"] == "Release Readiness" for risk in risks)
    target_risk = next(risk for risk in risks if risk["module"] == "Release Readiness")

    signoff_resp = await client.post(
        f"/api/v1/ui-repair/final/residual-risks/{target_risk['risk_id']}/sign-off",
        json={"operator": "Egemen YAZ"},
    )
    assert signoff_resp.status_code == 200
    assert signoff_resp.json()["accepted_by"] == "Egemen YAZ"
