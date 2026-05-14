from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any, Optional, cast

from libs.db.session import get_db
from libs.db.models.ui_repair_models import UIRepairCase, UIRouteHealth, UISmokeRun, UIRepairStatus
from services.ui_repair.service import UIRepairService
from services.ui_repair.schemas import (
    UIRepairOverview, UIRouteHealthSchema, UIRepairCaseSchema, UISmokeRunSchema,
    UIChaosDrillScenarioSchema, UIChaosDrillRunSchema, UISoakValidationRunSchema, UIRecoveryProofPackSchema,
    UIAdvancedChaosScenarioSchema, UIAdvancedChaosRunSchema, UIOperatorEscalationSchema, UINotificationDeliverySchema, UICrisisControlStateSchema,
    UIRedTeamScenarioSchema, UIRedTeamRunSchema, UIEnterpriseReadinessAssessmentSchema,
    UIReleaseGateDecisionSchema, UIFinalAuditPackSchema, UIOperatorHandoverReportSchema
)

router = APIRouter(prefix="/ui-repair", tags=["UI Repair"])

@router.get("/overview", response_model=UIRepairOverview)
async def get_ui_repair_overview(db: AsyncSession = Depends(get_db)):
    """High-level health overview of the UI system."""
    svc = UIRepairService(db)
    return await svc.get_overview()

@router.get("/routes", response_model=List[UIRouteHealthSchema])
async def get_ui_route_health(db: AsyncSession = Depends(get_db)):
    """Detailed health matrix for all tracked UI routes."""
    stmt = select(UIRouteHealth).order_by(UIRouteHealth.route)
    res = await db.execute(stmt)
    routes = []
    for route in res.scalars().all():
        routes.append(UIRouteHealthSchema(
            route=str(route.route),
            status=str(route.last_status or "UNKNOWN"),
            http_status=int(cast(Any, route).last_http_status or 0),
            blank_page_detected=bool(cast(Any, route).blank_page_detected),
            console_error_count=int(cast(Any, route).console_error_count or 0),
            network_error_count=int(cast(Any, route).network_error_count or 0),
            last_checked_at=cast(Any, route).last_checked_at,
            last_case_id=cast(Any, route).last_case_id
        ))
    return routes

@router.get("/cases", response_model=List[UIRepairCaseSchema])
async def get_ui_repair_cases(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Lists all detected UI repair cases, filtered by status."""
    stmt = select(UIRepairCase)
    if status:
        stmt = stmt.where(UIRepairCase.status == status)
    stmt = stmt.order_by(UIRepairCase.created_at.desc())
    
    res = await db.execute(stmt)
    results = []
    
    # Map model to schema (handling JSON fields)
    for c in res.scalars().all():
        results.append(UIRepairCaseSchema(
            id=cast(Any, c).id,
            route=str(c.route),
            status=str(c.status),
            severity=str(c.severity),
            failure_type=str(c.failure_type),
            title=str(c.title or ""),
            summary=str(getattr(c, 'summary', "")),
            console_errors=cast(Any, c).console_errors_json or [],
            network_errors=cast(Any, c).network_errors_json or [],
            screenshot_path=str(c.screenshot_path or ""),
            trace_path=str(c.trace_path or ""),
            evidence_json=getattr(c, 'evidence_json', {}),
            created_at=cast(Any, c).created_at,
            updated_at=cast(Any, c).updated_at,
            linked_incident_id=cast(Any, c).linked_incident_id,
            linked_runtime_diagnostic_id=str(c.linked_runtime_diagnostic_id or "")
        ))
    return results

@router.get("/cases/{case_id}", response_model=UIRepairCaseSchema)
async def get_ui_repair_case_detail(case_id: str, db: AsyncSession = Depends(get_db)):
    """Fetches details for a specific UI repair case."""
    stmt = select(UIRepairCase).where(UIRepairCase.id == case_id)
    case = (await db.execute(stmt)).scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    return UIRepairCaseSchema(
        id=cast(Any, case).id,
        route=str(case.route),
        status=str(case.status),
        severity=str(case.severity),
        failure_type=str(case.failure_type),
        title=str(case.title or ""),
        summary=str(getattr(case, 'summary', "")),
        console_errors=cast(Any, case).console_errors_json or [],
        network_errors=cast(Any, case).network_errors_json or [],
        screenshot_path=str(case.screenshot_path or ""),
        trace_path=str(case.trace_path or ""),
        evidence_json=getattr(case, 'evidence_json', {}),
        created_at=cast(Any, case).created_at,
        updated_at=cast(Any, case).updated_at,
        linked_incident_id=cast(Any, case).linked_incident_id,
        linked_runtime_diagnostic_id=str(case.linked_runtime_diagnostic_id or "")
    )

@router.post("/smoke/run")
async def trigger_ui_smoke_run(routes: Optional[List[str]] = None, db: AsyncSession = Depends(get_db)):
    """Manually triggers a Playwright smoke test run."""
    svc = UIRepairService(db)
    # Note: In a production environment, this should be moved to a Celery worker.
    # For the Faz 3 backbone, we execute it synchronously to confirm functionality.
    run = await svc.run_smoke_test(routes)
    return {"run_id": str(run.id), "status": run.status, "failed": run.failed_routes}

@router.post("/cases/{case_id}/mark-manual")
async def mark_case_manual(case_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(UIRepairCase).where(UIRepairCase.id == case_id)
    case = (await db.execute(stmt)).scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    case.status = cast(Any, UIRepairStatus.MANUAL_REVIEW_REQUIRED.value)
    await db.commit()
    return {"status": "success"}

@router.post("/cases/{case_id}/resolve")
async def resolve_case(case_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(UIRepairCase).where(UIRepairCase.id == case_id)
    case = (await db.execute(stmt)).scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    case.status = cast(Any, UIRepairStatus.RESOLVED.value)
    await db.commit()
    return {"status": "success"}

@router.post("/cases/{case_id}/repair")
async def trigger_autonomous_repair(case_id: str, db: AsyncSession = Depends(get_db)):
    """Triggers the autonomous repair hand-off for a specific case."""
    svc = UIRepairService(db)
    return await svc.trigger_autonomous_repair(case_id)

@router.get("/cases/{case_id}/attempts")
async def get_case_attempts(case_id: str, db: AsyncSession = Depends(get_db)):
    """Fetches all repair attempts for a specific case."""
    svc = UIRepairService(db)
    return await svc.get_attempt_logs(case_id)

@router.get("/cases/{case_id}/events")
async def get_case_events(case_id: str, db: AsyncSession = Depends(get_db)):
    """Fetches the event log for a specific case."""
    svc = UIRepairService(db)
    return await svc.get_case_events(case_id)

@router.get("/attempts/{attempt_id}/detail")
async def get_repair_attempt_full_detail(attempt_id: str, db: AsyncSession = Depends(get_db)):
    """Phase 5: Fetches complete review and verifier details for an attempt."""
    svc = UIRepairService(db)
    return await svc.get_repair_full_detail(attempt_id)

@router.post("/cases/{case_id}/attempts/{attempt_id}/apply")
async def apply_repair_patch(case_id: str, attempt_id: str, operator: str = Query("system"), db: AsyncSession = Depends(get_db)):
    """Phase 5: Central governance gate to approve and apply a repair."""
    svc = UIRepairService(db)
    return await svc.apply_patch(case_id, attempt_id, operator)

@router.get("/monitoring/config", response_model=UIMonitoringConfigSchema)
async def get_monitoring_config(db: AsyncSession = Depends(get_db)):
    """Fetches the current UI monitoring configuration."""
    svc = UIRepairService(db)
    return await svc.get_monitoring_config()

@router.post("/monitoring/config", response_model=UIMonitoringConfigSchema)
async def update_monitoring_config(data: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    """Updates the UI monitoring configuration."""
    svc = UIRepairService(db)
    return await svc.update_monitoring_config(data)

@router.get("/monitoring/runs", response_model=List[UIMonitoringRunSchema])
async def get_monitoring_runs(limit: int = 20, db: AsyncSession = Depends(get_db)):
    """Fetches recent monitoring run records."""
    svc = UIRepairService(db)
    return await svc.get_monitoring_runs(limit)

@router.post("/monitoring/trigger")
async def trigger_monitoring_cycle(db: AsyncSession = Depends(get_db)):
    """Manually triggers a background monitoring cycle."""
    svc = UIRepairService(db)
    return await svc.trigger_monitoring_cycle()

@router.get("/monitoring/history", response_model=List[UIRouteHealthHistSchema])
async def get_route_health_history(route: str, limit: int = 50, db: AsyncSession = Depends(get_db)):
    """Fetches historical health trends for a specific route."""
    svc = UIRepairService(db)
    return await svc.get_route_health_history(route, limit)

# --- Phase 8: Chaos Drills ---

@router.get("/chaos/scenarios", response_model=List[UIChaosDrillScenarioSchema])
async def get_chaos_scenarios(db: AsyncSession = Depends(get_db)):
    """Fetches all chaos drill scenarios."""
    svc = UIRepairService(db)
    return await svc.get_chaos_scenarios()

@router.post("/chaos/scenarios/{scenario_id}/run", response_model=Dict[str, Any])
async def run_chaos_drill(scenario_id: str, db: AsyncSession = Depends(get_db)):
    """Manually triggers a specific chaos drill."""
    svc = UIRepairService(db)
    return await svc.run_chaos_drill(scenario_id)

@router.get("/chaos/runs", response_model=List[UIChaosDrillRunSchema])
async def get_chaos_runs(limit: int = 20, db: AsyncSession = Depends(get_db)):
    """Fetches recent chaos drill results."""
    svc = UIRepairService(db)
    return await svc.get_chaos_runs(limit)

# --- Phase 8: Soak Validation ---

@router.post("/soak/start", response_model=Dict[str, Any])
async def start_soak_validation(duration_minutes: int = 60, db: AsyncSession = Depends(get_db)):
    """Initiates a long-term soak validation period."""
    svc = UIRepairService(db)
    return await svc.start_soak_validation(duration_minutes)

@router.get("/soak/runs", response_model=List[UISoakValidationRunSchema])
async def get_soak_runs(limit: int = 20, db: AsyncSession = Depends(get_db)):
    """Fetches soak validation history."""
    svc = UIRepairService(db)
    return await svc.get_soak_runs(limit)

# --- Phase 8: Recovery Proof Packs ---

@router.post("/proof-pack/generate", response_model=Dict[str, Any])
async def generate_proof_pack(name: str, days: int = 7, db: AsyncSession = Depends(get_db)):
    """Generates a recovery proof pack."""
    svc = UIRepairService(db)
    return await svc.generate_recovery_proof_pack(name, days)

@router.get("/proof-pack", response_model=List[UIRecoveryProofPackSchema])
async def get_recovery_proof_packs(limit: int = 20, db: AsyncSession = Depends(get_db)):
    """Fetches generated proof packs."""
    svc = UIRepairService(db)
    return await svc.get_recovery_proof_packs(limit)

# --- Phase 9: Advanced Chaos & Escalation ---

@router.get("/advanced-chaos/scenarios", response_model=List[UIAdvancedChaosScenarioSchema])
async def get_advanced_chaos_scenarios(db: AsyncSession = Depends(get_db)):
    """Fetches all advanced chaos scenarios."""
    svc = UIRepairService(db)
    return await svc.get_advanced_chaos_scenarios()

@router.post("/advanced-chaos/scenarios/{scenario_id}/run", response_model=Dict[str, Any])
async def run_advanced_chaos_drill(scenario_id: str, db: AsyncSession = Depends(get_db)):
    """Triggers an advanced chaos drill."""
    svc = UIRepairService(db)
    return await svc.run_advanced_chaos_drill(scenario_id)

@router.get("/advanced-chaos/runs", response_model=List[UIAdvancedChaosRunSchema])
async def get_advanced_chaos_runs(limit: int = 20, db: AsyncSession = Depends(get_db)):
    """Fetches advanced chaos drill results."""
    svc = UIRepairService(db)
    return await svc.get_advanced_chaos_runs(limit)

@router.get("/escalations", response_model=List[UIOperatorEscalationSchema])
async def get_ui_escalations(limit: int = 20, db: AsyncSession = Depends(get_db)):
    """Fetches recent operator escalations."""
    svc = UIRepairService(db)
    return await svc.get_escalations(limit)

@router.get("/escalations/{escalation_id}", response_model=UIOperatorEscalationSchema)
async def get_ui_escalation_detail(escalation_id: str, db: AsyncSession = Depends(get_db)):
    """Fetches details for a specific escalation."""
    svc = UIRepairService(db)
    esc = await svc.get_escalation(escalation_id)
    if not esc:
        raise HTTPException(status_code=404, detail="Escalation not found")
    return esc

@router.post("/escalations/{escalation_id}/ack")
async def acknowledge_ui_escalation(escalation_id: str, operator_id: str = Query(...), db: AsyncSession = Depends(get_db)):
    """Acknowledges an escalation."""
    svc = UIRepairService(db)
    await svc.acknowledge_escalation(escalation_id, operator_id)
    return {"status": "success"}

@router.post("/escalations/{escalation_id}/resolve")
async def resolve_ui_escalation(escalation_id: str, operator_id: str = Query(...), db: AsyncSession = Depends(get_db)):
    """Resolves an escalation."""
    svc = UIRepairService(db)
    await svc.resolve_escalation(escalation_id, operator_id)
    return {"status": "success"}

@router.get("/notifications/deliveries", response_model=List[UINotificationDeliverySchema])
async def get_notification_deliveries(limit: int = 20, db: AsyncSession = Depends(get_db)):
    """Fetches notification delivery history."""
    svc = UIRepairService(db)
    return await svc.get_notification_deliveries(limit)

@router.get("/crisis/state", response_model=UICrisisControlStateSchema)
async def get_ui_crisis_state(db: AsyncSession = Depends(get_db)):
    """Fetches the current UI crisis control state."""
    svc = UIRepairService(db)
    return await svc.get_crisis_state()

@router.post("/crisis/update", response_model=UICrisisControlStateSchema)
async def update_ui_crisis_state(mode: str, reason: str, operator_id: str = Query(...), db: AsyncSession = Depends(get_db)):
    """Updates the UI crisis control state."""
    svc = UIRepairService(db)
    return await svc.update_crisis_state(mode, reason, operator_id)

# --- Phase 10: Final Enterprise Readiness & Release Gate Endpoints ---

@router.get("/readiness/overview")
async def get_ui_readiness_overview(db: AsyncSession = Depends(get_db)):
    """Gets the latest enterprise readiness assessment and release gate decision."""
    svc = UIRepairService(db)
    return await svc.get_latest_readiness_overview()

@router.post("/readiness/assess", response_model=UIEnterpriseReadinessAssessmentSchema)
async def assess_ui_enterprise_readiness(assessor: str = Query(...), db: AsyncSession = Depends(get_db)):
    """Triggers a new enterprise readiness assessment."""
    svc = UIRepairService(db)
    return await svc.assess_enterprise_readiness(assessor)

@router.post("/red-team/generate", response_model=List[UIRedTeamScenarioSchema])
async def generate_ui_red_team_scenarios(db: AsyncSession = Depends(get_db)):
    """Generates new AI-powered red-team scenarios."""
    svc = UIRepairService(db)
    return await svc.generate_red_team_scenarios()

@router.post("/red-team/scenarios/{id}/run", response_model=UIRedTeamRunSchema)
async def run_ui_red_team_scenario(id: UUID, db: AsyncSession = Depends(get_db)):
    """Executes a red-team scenario."""
    svc = UIRepairService(db)
    return await svc.run_red_team_scenario(id)

@router.post("/release-gate/evaluate", response_model=UIReleaseGateDecisionSchema)
async def evaluate_ui_release_gate(assessment_id: UUID, approver: str = Query(...), db: AsyncSession = Depends(get_db)):
    """Evaluates the release gate for a given assessment."""
    svc = UIRepairService(db)
    return await svc.evaluate_release_gate(assessment_id, approver)

@router.post("/final-audit-pack/generate", response_model=UIFinalAuditPackSchema)
async def generate_ui_final_audit_pack(name: str = Query(...), version: str = Query(...), db: AsyncSession = Depends(get_db)):
    """Generates a sealed final audit pack."""
    svc = UIRepairService(db)
    return await svc.generate_final_audit_pack(name, version)

@router.post("/handover/generate", response_model=UIOperatorHandoverReportSchema)
async def generate_ui_operator_handover(title: str = Query(...), db: AsyncSession = Depends(get_db)):
    """Generates an operator handover report."""
    svc = UIRepairService(db)
    return await svc.generate_handover_report(title)
