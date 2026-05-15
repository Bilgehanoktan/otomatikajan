from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import List, Dict, Any, Optional, cast

from libs.db.session import get_db
from libs.db.models.ui_repair_models import (
    UIRepairCase, UIRouteHealth, UISmokeRun, UIRepairStatus,
    UIPolicyRule, UIPolicyEvaluation, UIPolicyConflict, UIPolicyProposal,
    UIAutonomousOverride, UIComplianceFinding
)
from services.ui_repair.service import UIRepairService
from services.ui_repair.schemas import (
    UIRepairOverview, UIRouteHealthSchema, UIRepairCaseSchema, UISmokeRunSchema,
    UIChaosDrillScenarioSchema, UIChaosDrillRunSchema, UISoakValidationRunSchema, UIRecoveryProofPackSchema,
    UIAdvancedChaosScenarioSchema, UIAdvancedChaosRunSchema, UIOperatorEscalationSchema, UINotificationDeliverySchema, UICrisisControlStateSchema,
    UIRedTeamScenarioSchema, UIRedTeamRunSchema, UIEnterpriseReadinessAssessmentSchema,
    UIReleaseGateDecisionSchema, UIFinalAuditPackSchema, UIOperatorHandoverReportSchema,
    UIPilotRolloutSchema, UIPilotRolloutCreate, UIPilotEventSchema, UIPilotEventCreate,
    UIPilotMetricsSchema, UIOperatorActionLedgerSchema, UIOperatorActionLedgerCreate, UIPilotFinalReportSchema,
    UIProjectProfileSchema, UIProjectProfileCreate, UIRolloutWaveSchema, UIRolloutWaveCreate,
    UIProjectHealthSnapshotSchema, UIGAReadinessAssessmentSchema, UIEnterpriseRunbookSchema, UIEnterpriseOverviewSchema,
    UIOperationsTeamSchema, UIOperationsTeamCreate, UIProjectOwnershipSchema, UIProjectOwnershipCreate,
    UIMaintenancePolicySchema, UIMaintenancePolicyCreate, UIReleaseRecordSchema, UIReleaseRecordCreate,
    UICompatibilityCheckSchema, UICompatibilityCheckCreate, UIEvidenceRetentionPolicySchema, UIEvidenceRetentionPolicyCreate,
    UISLOBreachSchema, UISLOBreachCreate,
    UIPolicyRuleSchema, UIPolicyRuleCreate, UIPolicyEvaluationSchema, UIPolicyConflictSchema, 
    UIPolicyProposalSchema, UIPolicyProposalCreate, UIAutonomousOverrideSchema, UIAutonomousOverrideCreate,
    UIComplianceFindingSchema,
    UIMonitoringConfigSchema, UIMonitoringRunSchema, UIRouteHealthHistSchema,
    UIBudgetPolicyCreate,
    UITenantProfileSchema, UITenantProfileCreate, UIClusterProfileSchema, UIClusterProfileCreate,
    UITenantProjectBindingSchema, UITenantProjectBindingCreate, UIClusterHealthSnapshotSchema, UIClusterHealthSnapshotCreate
)

from services.ui_repair.resiliency_mesh_router import router as mesh_router

router = APIRouter(prefix="/ui-repair", tags=["UI Repair"])
router.include_router(mesh_router)

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

# Phase 11: Pilot Rollout Endpoints

@router.get("/pilot/status", response_model=UIPilotRolloutSchema)
async def get_pilot_status(db: AsyncSession = Depends(get_db)):
    svc = UIRepairService(db)
    return await svc.get_pilot_status()

@router.post("/pilot/start", response_model=UIPilotRolloutSchema)
async def start_pilot(
    name: str = Query(...), 
    mode: str = "GOVERNED_REPAIR", 
    duration: int = 7,
    created_by: str = "Admin",
    db: AsyncSession = Depends(get_db)
):
    svc = UIRepairService(db)
    return await svc.start_pilot(name, mode, duration, created_by)

@router.post("/pilot/pause")
async def pause_pilot(rollout_id: str = Query(...), rationale: str = Query(...), db: AsyncSession = Depends(get_db)):
    svc = UIRepairService(db)
    return await svc.pause_pilot(rollout_id, rationale)

@router.get("/pilot/metrics/{rollout_id}", response_model=UIPilotMetricsSchema)
async def get_pilot_metrics(rollout_id: str, db: AsyncSession = Depends(get_db)):
    svc = UIRepairService(db)
    return await svc.get_pilot_metrics(rollout_id)

@router.post("/pilot/report/generate")
async def generate_pilot_report(rollout_id: str = Query(...), db: AsyncSession = Depends(get_db)):
    svc = UIRepairService(db)
    return await svc.generate_pilot_report(rollout_id)

@router.post("/pilot/operator-actions")
async def record_operator_action(
    rollout_id: str = Query(...), 
    operator: str = Query(...), 
    action_type: str = Query(...), 
    rationale: str = Query(...),
    target_type: str = Query(None),
    target_id: str = Query(None),
    db: AsyncSession = Depends(get_db)
):
    svc = UIRepairService(db)
    return await svc.record_operator_action(rollout_id, operator, action_type, rationale, target_type, target_id)

# Phase 12: General Availability + Multi-Project Rollout Endpoints

@router.get("/projects", response_model=List[UIProjectProfileSchema])
async def list_ui_repair_projects(db: AsyncSession = Depends(get_db)):
    """Lists all UI repair project profiles."""
    svc = UIRepairService(db)
    return await svc.list_projects()

@router.post("/projects", response_model=UIProjectProfileSchema)
async def create_ui_repair_project(data: UIProjectProfileCreate, db: AsyncSession = Depends(get_db)):
    """Creates a new UI repair project profile."""
    svc = UIRepairService(db)
    return await svc.create_project(data)

@router.get("/projects/{project_key}", response_model=UIProjectProfileSchema)
async def get_ui_repair_project(project_key: str, db: AsyncSession = Depends(get_db)):
    """Gets a specific project profile."""
    svc = UIRepairService(db)
    return await svc.get_project(project_key)

@router.post("/projects/{project_key}/activate", response_model=UIProjectProfileSchema)
async def activate_ui_repair_project(project_key: str, db: AsyncSession = Depends(get_db)):
    """Activates a project."""
    svc = UIRepairService(db)
    return await svc.update_project_status(project_key, "ACTIVE")

@router.post("/projects/{project_key}/pause", response_model=UIProjectProfileSchema)
async def pause_ui_repair_project(project_key: str, db: AsyncSession = Depends(get_db)):
    """Pauses a project."""
    svc = UIRepairService(db)
    return await svc.update_project_status(project_key, "PAUSED")

@router.post("/projects/{project_key}/policy")
async def update_ui_repair_project_policy(
    project_key: str, 
    safety: Optional[Dict[str, Any]] = None, 
    governance: Optional[Dict[str, Any]] = None, 
    db: AsyncSession = Depends(get_db)
):
    """Updates a project's safety and governance policy."""
    svc = UIRepairService(db)
    return await svc.update_project_policy(project_key, safety, governance)

@router.get("/rollout-waves", response_model=List[UIRolloutWaveSchema])
async def list_ui_rollout_waves(db: AsyncSession = Depends(get_db)):
    """Lists all GA rollout waves."""
    svc = UIRepairService(db)
    return await svc.list_rollout_waves()

@router.post("/rollout-waves", response_model=UIRolloutWaveSchema)
async def create_ui_rollout_wave(data: UIRolloutWaveCreate, db: AsyncSession = Depends(get_db)):
    """Creates a new rollout wave."""
    svc = UIRepairService(db)
    return await svc.create_rollout_wave(data)

@router.post("/rollout-waves/{wave_id}/start", response_model=UIRolloutWaveSchema)
async def start_ui_rollout_wave(wave_id: str, db: AsyncSession = Depends(get_db)):
    """Starts a rollout wave."""
    svc = UIRepairService(db)
    return await svc.start_rollout_wave(wave_id)

@router.post("/rollout-waves/{wave_id}/complete", response_model=UIRolloutWaveSchema)
async def complete_ui_rollout_wave(wave_id: str, db: AsyncSession = Depends(get_db)):
    """Completes a rollout wave."""
    svc = UIRepairService(db)
    return await svc.complete_rollout_wave(wave_id)

@router.get("/enterprise/overview", response_model=UIEnterpriseOverviewSchema)
async def get_ui_enterprise_overview(db: AsyncSession = Depends(get_db)):
    """Gets a global summary of all projects and waves."""
    svc = UIRepairService(db)
    return await svc.get_enterprise_overview()

@router.get("/enterprise/sla-slo")
async def get_ui_enterprise_sla_slo(db: AsyncSession = Depends(get_db)):
    """Gets global SLA/SLO metrics."""
    svc = UIRepairService(db)
    return await svc.get_sla_slo_metrics()

@router.post("/enterprise/ga-readiness/check", response_model=UIGAReadinessAssessmentSchema)
async def check_ui_ga_readiness(assessor: str = Query(...), db: AsyncSession = Depends(get_db)):
    """Triggers a new GA readiness assessment."""
    svc = UIRepairService(db)
    return await svc.check_ga_readiness(assessor)

@router.get("/enterprise/ga-readiness/latest", response_model=Optional[UIGAReadinessAssessmentSchema])
async def get_latest_ui_ga_readiness(db: AsyncSession = Depends(get_db)):
    """Gets the latest GA readiness assessment."""
    svc = UIRepairService(db)
    return await svc.get_latest_ga_readiness()

@router.post("/enterprise/runbook/generate", response_model=UIEnterpriseRunbookSchema)
async def generate_ui_enterprise_runbook(title: str = Query(...), version: str = Query(...), db: AsyncSession = Depends(get_db)):
    """Generates an enterprise runbook."""
    svc = UIRepairService(db)
    return await svc.generate_enterprise_runbook(title, version)

@router.get("/enterprise/runbook/latest", response_model=Optional[UIEnterpriseRunbookSchema])
async def get_latest_ui_enterprise_runbook(db: AsyncSession = Depends(get_db)):
    """Gets the latest enterprise runbook."""
    svc = UIRepairService(db)
    return await svc.get_latest_runbook()

# --- Phase 13: GA Hardening + Cross-Team Operations Endpoints ---

@router.get("/operations/teams", response_model=List[UIOperationsTeamSchema])
async def list_operations_teams(db: AsyncSession = Depends(get_db)):
    svc = UIRepairService(db)
    return await svc.list_operations_teams()

@router.post("/operations/teams", response_model=UIOperationsTeamSchema)
async def create_operations_team(data: UIOperationsTeamCreate, db: AsyncSession = Depends(get_db)):
    svc = UIRepairService(db)
    return await svc.create_operations_team(data)

@router.get("/operations/ownership", response_model=List[UIProjectOwnershipSchema])
async def list_project_ownerships(db: AsyncSession = Depends(get_db)):
    svc = UIRepairService(db)
    return await svc.list_project_ownerships()

@router.post("/operations/ownership", response_model=UIProjectOwnershipSchema)
async def create_project_ownership(data: UIProjectOwnershipCreate, db: AsyncSession = Depends(get_db)):
    svc = UIRepairService(db)
    return await svc.create_project_ownership(data)

@router.get("/operations/escalation-matrix")
async def get_escalation_matrix(project_key: str, severity: str = "HIGH", db: AsyncSession = Depends(get_db)):
    svc = UIRepairService(db)
    return await svc.get_escalation_path(project_key, severity)

@router.get("/maintenance/policies", response_model=List[UIMaintenancePolicySchema])
async def list_maintenance_policies(db: AsyncSession = Depends(get_db)):
    svc = UIRepairService(db)
    return await svc.list_maintenance_policies()

@router.post("/maintenance/policies", response_model=UIMaintenancePolicySchema)
async def create_maintenance_policy(data: UIMaintenancePolicyCreate, db: AsyncSession = Depends(get_db)):
    svc = UIRepairService(db)
    return await svc.create_maintenance_policy(data)

@router.get("/releases", response_model=List[UIReleaseRecordSchema])
async def list_releases(db: AsyncSession = Depends(get_db)):
    svc = UIRepairService(db)
    return await svc.list_releases()

@router.post("/releases/generate-notes", response_model=UIReleaseRecordSchema)
async def generate_release_notes(data: UIReleaseRecordCreate, db: AsyncSession = Depends(get_db)):
    svc = UIRepairService(db)
    return await svc.generate_release_record(data)

@router.post("/compatibility/check", response_model=UICompatibilityCheckSchema)
async def run_compatibility_check(project_key: str, version: str, db: AsyncSession = Depends(get_db)):
    svc = UIRepairService(db)
    return await svc.run_compatibility_check(project_key, version)

@router.get("/compatibility/latest", response_model=Optional[UICompatibilityCheckSchema])
async def get_latest_compatibility_check(project_key: str, db: AsyncSession = Depends(get_db)):
    svc = UIRepairService(db)
    return await svc.get_latest_compatibility_check(project_key)

@router.get("/evidence/retention", response_model=List[UIEvidenceRetentionPolicySchema])
async def list_evidence_retention_policies(db: AsyncSession = Depends(get_db)):
    svc = UIRepairService(db)
    return await svc.list_evidence_retention_policies()

@router.post("/evidence/retention", response_model=UIEvidenceRetentionPolicySchema)
async def create_evidence_retention_policy(data: UIEvidenceRetentionPolicyCreate, db: AsyncSession = Depends(get_db)):
    svc = UIRepairService(db)
    return await svc.create_evidence_retention_policy(data)

@router.get("/slo/breaches", response_model=List[UISLOBreachSchema])
async def list_slo_breaches(project_key: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    svc = UIRepairService(db)
    return await svc.list_slo_breaches(project_key)

@router.post("/slo/breaches/{breach_id}/ack", response_model=UISLOBreachSchema)
async def acknowledge_slo_breach(breach_id: str, db: AsyncSession = Depends(get_db)):
    svc = UIRepairService(db)
    res = await svc.acknowledge_slo_breach(breach_id)
    if not res:
        raise HTTPException(status_code=404, detail="Breach not found")
    return res

@router.post("/slo/breaches/{breach_id}/resolve", response_model=UISLOBreachSchema)
async def resolve_slo_breach(breach_id: str, db: AsyncSession = Depends(get_db)):
    svc = UIRepairService(db)
    res = await svc.resolve_slo_breach(breach_id)
    if not res:
        raise HTTPException(status_code=404, detail="Breach not found")
    return res

# --- Phase 14: Enterprise FinOps Endpoints ---

@router.get("/finops/overview", response_model=UIFinOpsOverviewSchema)
async def get_finops_overview(db: AsyncSession = Depends(get_db)):
    """High-level FinOps dashboard data."""
    svc = UIRepairService(db)
    return await svc.get_finops_overview()

# --- Phase 16: Multi-Tenant Federation + Cross-Cluster Governance Endpoints ---

@router.get("/federation/tenants", response_model=List[UITenantProfileSchema])
async def list_tenants(db: AsyncSession = Depends(get_db)):
    """Lists all registered enterprise tenants."""
    svc = UIRepairService(db)
    return await svc.list_tenants()

@router.post("/federation/tenants", response_model=UITenantProfileSchema)
async def create_tenant(data: UITenantProfileCreate, db: AsyncSession = Depends(get_db)):
    """Registers a new enterprise tenant."""
    svc = UIRepairService(db)
    return await svc.create_tenant(data)

@router.post("/federation/tenants/bind", response_model=UITenantProjectBindingSchema)
async def bind_project_to_tenant(data: UITenantProjectBindingCreate, db: AsyncSession = Depends(get_db)):
    """Binds a project to a tenant and cluster."""
    svc = UIRepairService(db)
    return await svc.bind_project_to_tenant(data)

@router.get("/federation/clusters", response_model=List[UIClusterProfileSchema])
async def list_clusters(db: AsyncSession = Depends(get_db)):
    """Lists all regional or environmental clusters."""
    svc = UIRepairService(db)
    return await svc.list_clusters()

@router.post("/federation/clusters", response_model=UIClusterProfileSchema)
async def create_cluster(data: UIClusterProfileCreate, db: AsyncSession = Depends(get_db)):
    """Registers a new cluster."""
    svc = UIRepairService(db)
    return await svc.create_cluster(data)

@router.get("/federation/cluster-health")
async def get_federated_health(db: AsyncSession = Depends(get_db)):
    """Aggregated health metrics across all clusters."""
    svc = UIRepairService(db)
    return await svc.get_federated_health()

@router.get("/federation/policy-drift")
async def scan_policy_drift(tenant_key: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """Scans for deviations from global/tenant policy standards."""
    svc = UIRepairService(db)
    return await svc.scan_policy_drift(tenant_key)

@router.get("/federation/evidence")
async def get_federated_evidence(tenant_key: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """Centralized audit trail of evidence hashes across the federation."""
    svc = UIRepairService(db)
    return await svc.get_federated_evidence(tenant_key)

@router.get("/finops/costs", response_model=List[UICostEventSchema])
async def list_cost_events(
    project_key: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List recent cost events with attribution."""
    svc = UIRepairService(db)
    return await svc.list_cost_events(project_key)

@router.get("/finops/budget/{project_key}", response_model=Optional[UIBudgetPolicySchema])
async def get_budget_policy(project_key: str, db: AsyncSession = Depends(get_db)):
    """Get budget policy for a project."""
    svc = UIRepairService(db)
    return await svc.get_budget_policy(project_key)

@router.post("/finops/budget", response_model=UIBudgetPolicySchema)
async def update_budget_policy(data: UIBudgetPolicyCreate, db: AsyncSession = Depends(get_db)):
    """Create or update budget policy."""
    svc = UIRepairService(db)
    return await svc.update_budget_policy(data)

@router.get("/finops/anomalies", response_model=List[UICostAnomalySchema])
async def list_cost_anomalies(
    project_key: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List cost anomalies and spikes."""
    svc = UIRepairService(db)
    return await svc.list_cost_anomalies(project_key)

@router.post("/finops/anomalies/{anomaly_id}/resolve", response_model=UICostAnomalySchema)
async def resolve_cost_anomaly(anomaly_id: str, db: AsyncSession = Depends(get_db)):
    """Resolve a cost anomaly."""
    svc = UIRepairService(db)
    res = await svc.resolve_cost_anomaly(anomaly_id)
    if not res:
        raise HTTPException(status_code=404, detail="Anomaly not found")
    return res

@router.get("/finops/forecast/{project_key}", response_model=Optional[UICapacityForecastSchema])
async def get_capacity_forecast(project_key: str, db: AsyncSession = Depends(get_db)):
    """Get latest capacity forecast."""
    svc = UIRepairService(db)
    return await svc.get_capacity_forecast(project_key)

@router.post("/finops/forecast/{project_key}/generate", response_model=UICapacityForecastSchema)
async def generate_capacity_forecast(project_key: str, db: AsyncSession = Depends(get_db)):
    """Manually trigger a capacity forecast generation."""
    svc = UIRepairService(db)
    return await svc.generate_capacity_forecast(project_key)

@router.get("/finops/recommendations", response_model=List[UIFinOpsRecommendationSchema])
async def list_finops_recommendations(
    project_key: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List cost-saving recommendations."""
    svc = UIRepairService(db)
    return await svc.list_finops_recommendations(project_key)

@router.post("/finops/recommendations/{rec_id}/status", response_model=UIFinOpsRecommendationSchema)
async def update_recommendation_status(
    rec_id: str, 
    status: str = Query(..., regex="^(PENDING|APPLIED|DISMISSED)$"),
    db: AsyncSession = Depends(get_db)
):
    """Update recommendation status (Apply or Dismiss)."""
    svc = UIRepairService(db)
    res = await svc.update_recommendation_status(rec_id, status)
    if not res:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return res

# --- Phase 15: Autonomous Ecosystem Governance Endpoints ---

@router.get("/governance/policies", response_model=List[UIPolicyRuleSchema])
async def list_policy_rules(
    project_key: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Lists all active governance policies."""
    svc = UIRepairService(db)
    return await svc.list_policy_rules(project_key)

@router.post("/governance/policies", response_model=UIPolicyRuleSchema)
async def create_policy_rule(
    rule_data: UIPolicyRuleCreate,
    db: AsyncSession = Depends(get_db)
):
    """Registers a new governance policy rule."""
    svc = UIRepairService(db)
    return await svc.create_policy_rule(rule_data)

@router.post("/governance/evaluate", response_model=UIPolicyEvaluationSchema)
async def evaluate_governance_policy(
    action_type: str,
    context: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """Evaluates an autonomous action against current policies."""
    svc = UIRepairService(db)
    return await svc.evaluate_action(action_type, context)

@router.get("/governance/evaluations", response_model=List[UIPolicyEvaluationSchema])
async def list_policy_evaluations(
    project_key: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Audit log of policy evaluations."""
    stmt = select(UIPolicyEvaluation)
    if project_key:
        stmt = stmt.where(UIPolicyEvaluation.project_key == project_key)
    stmt = stmt.order_by(UIPolicyEvaluation.evaluated_at.desc())
    res = await db.execute(stmt)
    return list(res.scalars().all())

@router.post("/governance/overrides", response_model=UIAutonomousOverrideSchema)
async def create_policy_override(
    override_data: UIAutonomousOverrideCreate,
    db: AsyncSession = Depends(get_db)
):
    """Records a manual override of a blocked autonomous action."""
    svc = UIRepairService(db)
    return await svc.create_autonomous_override(override_data)

@router.get("/governance/compliance-findings", response_model=List[UIComplianceFindingSchema])
async def list_compliance_findings(
    project_key: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Lists compliance violations found in the ecosystem."""
    svc = UIRepairService(db)
    return await svc.get_compliance_findings(project_key)

@router.get("/governance/proposals", response_model=List[UIPolicyProposalSchema])
async def list_policy_proposals(
    project_key: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Lists all policy proposals."""
    stmt = select(UIPolicyProposal)
    if project_key:
        stmt = stmt.where(UIPolicyProposal.project_key == project_key)
    res = await db.execute(stmt)
    return list(res.scalars().all())

@router.post("/governance/proposals", response_model=UIPolicyProposalSchema)
async def create_policy_proposal(
    proposal_data: UIPolicyProposalCreate,
    db: AsyncSession = Depends(get_db)
):
    """Submits a new policy proposal."""
    svc = UIRepairService(db)
    return await svc.create_policy_proposal(proposal_data)

@router.post("/governance/proposals/{proposal_id}/approve", response_model=UIPolicyRuleSchema)
async def approve_proposal(
    proposal_id: UUID,
    reviewer: str,
    db: AsyncSession = Depends(get_db)
):
    """Approves and applies a policy proposal."""
    svc = UIRepairService(db)
    return await svc.approve_policy_proposal(proposal_id, reviewer)

@router.get("/governance/conflicts", response_model=List[UIPolicyConflictSchema])
async def list_policy_conflicts(
    project_key: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Lists detected policy conflicts."""
    svc = UIRepairService(db)
    return await svc.list_policy_conflicts(project_key)

@router.post("/governance/simulate")
async def simulate_policy(
    rule_definition: Dict[str, Any] = Body(...),
    project_key: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Simulates a policy rule against historical evaluations."""
    from .policy_simulator import PolicySimulator
    simulator = PolicySimulator(db)
    return await simulator.simulate_rule(rule_definition, project_key)
