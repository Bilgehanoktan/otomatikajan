from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import List, Dict, Any, Optional, cast
from datetime import datetime, timezone

from libs.db.session import get_db
from libs.db.models.ui_repair_models import (
    UIRepairCase, UIRouteHealth, UISmokeRun, UIRepairStatus,
    UIPolicyRule, UIPolicyEvaluation, UIPolicyConflict, UIPolicyProposal,
    UIAutonomousOverride, UISecurityPostureFinding, ReleaseStatus
)
from services.ui_repair.service import UIRepairService
from services.ui_repair.schemas import (
    UIRepairOverview, UIRouteHealthSchema, UIRepairCaseSchema, UISmokeRunSchema,
    UIChaosDrillScenarioSchema, UIChaosDrillRunSchema, UISoakValidationRunSchema, UIRecoveryProofPackSchema,
    UIAdvancedChaosScenarioSchema, UIAdvancedChaosRunSchema, UIOperatorEscalationSchema, UINotificationDeliverySchema, UICrisisControlStateSchema,
    UIRedTeamScenarioSchema, UIRedTeamRunSchema, UIAdversarialDriftEventSchema, UIRedTeamOverviewSchema, UIEnterpriseReadinessAssessmentSchema,
    UIReleaseGateDecisionSchema, UIFinalAuditPackSchema, UIOperatorHandoverReportSchema,
    UIPilotRolloutSchema, UIPilotRolloutCreate, UIPilotEventSchema, UIPilotEventCreate,
    UIPilotMetricsSchema, UIOperatorActionLedgerSchema, UIOperatorActionLedgerCreate, UIPilotFinalReportSchema,
    UIProjectProfileSchema, UIProjectProfileCreate, UIRolloutWaveSchema, UIRolloutWaveCreate,
    UIProjectHealthSnapshotSchema, UIProjectHealthMatrixRowSchema, UIGAReadinessAssessmentSchema, UIEnterpriseRunbookSchema, UIEnterpriseOverviewSchema,
    UIOperationsTeamSchema, UIOperationsTeamCreate, UIProjectOwnershipSchema, UIProjectOwnershipCreate,
    UIMaintenancePolicySchema, UIMaintenancePolicyCreate, UIReleaseRecordSchema, UIReleaseRecordCreate,
    UICompatibilityCheckSchema, UICompatibilityCheckCreate, UIEvidenceRetentionPolicySchema, UIEvidenceRetentionPolicyCreate,
    UISLOBreachSchema, UISLOBreachCreate,
    UIPolicyRuleSchema, UIPolicyRuleCreate, UIPolicyEvaluationSchema, UIPolicyConflictSchema, 
    UIPolicyProposalSchema, UIPolicyProposalCreate, UIAutonomousOverrideSchema, UIAutonomousOverrideCreate,
    UICognitiveIntegrityCheckSchema,
    UIHallucinationFindingSchema,
    UILLMClaimSchema,
    UICognitiveIntegrityVerifyRequest,
    UISecurityPostureScoreSchema,
    UIComplianceControlSchema,
    UISecurityPostureFindingSchema,
    UISecurityCertificationSchema,
    UIMonitoringConfigSchema, UIMonitoringRunSchema, UIRouteHealthHistSchema,
    UIBudgetPolicyCreate,
    UITenantProfileSchema, UITenantProfileCreate, UIClusterProfileSchema, UIClusterProfileCreate,
    UITenantProjectBindingSchema, UITenantProjectBindingCreate, UIClusterHealthSnapshotSchema, UIClusterHealthSnapshotCreate, UIFederationOverviewSchema,
    UIFinOpsOverviewSchema, UIFinOpsRecommendationSchema,
    UICostEventSchema, UICostAnomalySchema, UIBudgetPolicySchema,
    UICapacityForecastSchema,
    UISecurityRemediationPlanSchema,
    UISecurityAutoFixAttemptSchema,
    UIComplianceFixResultSchema,
    UISecurityRemediationEventSchema,
    UIAttackSurfaceAssetSchema,
    UIThreatModelSchema,
    UIAttackPathSchema,
    UIAttackSimulationRunSchema,
    UIThreatMitigationSchema,
    UIThreatSummarySchema,
    UIGuardrailTuningProposalSchema,
    UIDefensivePatternSchema,
    UIPolicyRegressionRunSchema,
    UIGuardrailCanaryRunSchema,
    UIDefenseOptimizationReportSchema, UIDefenseOverviewSchema,
    UIIncidentWarRoomSchema, UIIncidentTimelineEventSchema, UIExecutiveRiskSnapshotSchema,
    UIIncidentActionItemSchema, UIExecutiveRiskReportSchema,
    UIIncidentActionItemCreate, WarRoomResolveRequest, ExecutiveRiskOverview,
    UIRedTeamRunSchema, UIAdversarialProbeSchema, UIAdversarialDriftEventSchema,
    UIRedTeamFindingSchema, UIRedTeamReportSchema,
    AutoPatchExecutionSchema, PatchCandidateSchema, VerificationRunV2Schema, 
    PostApplyValidationSchema, RollbackExecutionSchema,
    AutoPatchStartRequest, AutoPatchActionRequest,
    AutoPatchTraceSchema, PatchNegotiationSessionSchema, PatchDebateTurnSchema, PatchCandidateScoreSchema,
    NegotiationStartRequest,
    UIKnowledgeNodeSchema, UIKnowledgeEdgeSchema, UICausalMemorySchema, UICausalChainSchema,
    UIIncidentPatternSchema, UISimilarCaseMatchSchema, UIRiskPredictionSchema,
    UIKnowledgeGraphOverviewSchema, UIKnowledgeReportSchema, SimilarCaseRequest,
    UIFinalIntegrationAuditSchema, UIReleaseReadinessCheckSchema,
    UIFinalAuditPackSchema, UIReleaseLockSchema, UISmokeTestResultSchema,
    UIPhaseCompletionSchema, UIResidualRiskSchema, UIToolRiskOverviewSchema
)

from services.ui_repair.knowledge_graph_builder import KnowledgeGraphBuilder
from services.ui_repair.causal_memory_engine import CausalMemoryEngine
from services.ui_repair.risk_prediction_engine import RiskPredictionEngine

# Phase 30 Imports
from services.ui_repair.final_integration_auditor import FinalIntegrationAuditor
from services.ui_repair.release_readiness_checker import ReleaseReadinessChecker
from services.ui_repair.final_audit_pack_generator import FinalAuditPackGenerator
from services.ui_repair.system_smoke_test_runner import SystemSmokeTestRunner
from services.ui_repair.release_lock_manager import ReleaseLockManager

from services.ui_repair.resiliency_mesh_router import router as resiliency_mesh_router
from services.ui_repair.external_tool_governance_router import router as tool_governance_router
from services.ui_repair.identity_governance_router import router as identity_governance_router
from services.ui_repair.cognitive_governance import router as cognitive_governance_router

router = APIRouter(tags=["UI Repair"])
router.include_router(resiliency_mesh_router)
router.include_router(tool_governance_router)
router.include_router(identity_governance_router)
router.include_router(cognitive_governance_router)

@router.post("/bootstrap")
async def run_ui_repair_bootstrap(db: AsyncSession = Depends(get_db)):
    """Idempotently seeds baseline data for UI repair."""
    from services.ui_repair.baseline_bootstrap import UIRepairBaselineBootstrapper
    bootstrapper = UIRepairBaselineBootstrapper(db)
    res = await bootstrapper.ensure_baseline()
    return {"status": "success", "results": res}

@router.get("/overview", response_model=UIRepairOverview)
async def get_ui_repair_overview(db: AsyncSession = Depends(get_db)):
    """High-level health overview of the UI system."""
    svc = UIRepairService(db)
    return await svc.get_overview()

@router.get("/dashboard/summary", response_model=UIRepairOverview)
async def get_ui_repair_dashboard_summary(db: AsyncSession = Depends(get_db)):
    """Fast dashboard summary for the operator home surface."""
    svc = UIRepairService(db)
    return await svc.get_dashboard_summary()

@router.get("/routes", response_model=List[UIRouteHealthSchema])
async def get_ui_route_health(db: AsyncSession = Depends(get_db)):
    """Detailed health matrix for all tracked UI routes."""
    active_routes = UIRepairService.DEFAULT_ROUTES
    stmt = (
        select(UIRouteHealth)
        .where(UIRouteHealth.route.in_(active_routes))
        .order_by(UIRouteHealth.route)
    )
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
    status: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    """Lists all detected UI repair cases, filtered by status."""
    active_routes = UIRepairService.DEFAULT_ROUTES
    stmt = select(UIRepairCase)
    if status:
        stmt = stmt.where(UIRepairCase.status == status)
    else:
        failing_routes_stmt = select(UIRouteHealth.route).where(
            UIRouteHealth.route.in_(active_routes),
            UIRouteHealth.last_status == "FAIL",
        )
        failing_routes = set((await db.execute(failing_routes_stmt)).scalars().all())
        if not failing_routes:
            return []
        stmt = stmt.where(
            UIRepairCase.route.in_(failing_routes),
            UIRepairCase.status != "RESOLVED",
            UIRepairCase.status != "IGNORED",
        )
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

@router.get("/runtime-guard/status")
async def get_runtime_guard_status():
    """Returns the current runtime guard status checking all infrastructure dependencies."""
    from services.ui_repair.runtime_guard import check_runtime_dependencies
    return await check_runtime_dependencies()

@router.post("/smoke/run")
async def trigger_ui_smoke_run(routes: List[str] | None = None, db: AsyncSession = Depends(get_db)):
    """Manually triggers a Playwright smoke test run."""
    from services.ui_repair.runtime_guard import check_runtime_dependencies
    guard = await check_runtime_dependencies()
    if guard["status"] == "degraded":
        return guard

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
    from services.ui_repair.runtime_guard import check_runtime_dependencies
    guard = await check_runtime_dependencies(require_docker=True)
    if guard["status"] == "degraded":
        return guard

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
    from services.ui_repair.runtime_guard import check_runtime_dependencies
    guard = await check_runtime_dependencies()
    if guard["status"] == "degraded":
        return guard

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
    target_type: str | None = Query(None),
    target_id: str | None = Query(None),
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

@router.get("/projects/health-matrix", response_model=List[UIProjectHealthMatrixRowSchema])
async def get_project_health_matrix(db: AsyncSession = Depends(get_db)):
    """Returns the live project health matrix used by the operator dashboard."""
    svc = UIRepairService(db)
    return await svc.get_project_health_matrix()

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
    safety: Dict[str, Any] | None = None, 
    governance: Dict[str, Any] | None = None, 
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

@router.get("/enterprise/ga-readiness/latest", response_model=UIGAReadinessAssessmentSchema | None)
async def get_latest_ui_ga_readiness(db: AsyncSession = Depends(get_db)):
    """Gets the latest GA readiness assessment."""
    svc = UIRepairService(db)
    return await svc.get_latest_ga_readiness()

@router.post("/enterprise/runbook/generate", response_model=UIEnterpriseRunbookSchema)
async def generate_ui_enterprise_runbook(title: str = Query(...), version: str = Query(...), db: AsyncSession = Depends(get_db)):
    """Generates an enterprise runbook."""
    svc = UIRepairService(db)
    return await svc.generate_enterprise_runbook(title, version)

@router.get("/enterprise/runbook/latest", response_model=UIEnterpriseRunbookSchema | None)
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

@router.get("/compatibility/latest", response_model=UICompatibilityCheckSchema | None)
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
async def list_slo_breaches(project_key: str | None = None, db: AsyncSession = Depends(get_db)):
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

@router.get("/federation/overview", response_model=UIFederationOverviewSchema)
async def get_federation_overview(db: AsyncSession = Depends(get_db)):
    """Live federation summary for the control-plane overview."""
    svc = UIRepairService(db)
    return await svc.get_federation_overview()

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
async def scan_policy_drift(tenant_key: str | None = None, db: AsyncSession = Depends(get_db)):
    """Scans for deviations from global/tenant policy standards."""
    svc = UIRepairService(db)
    return await svc.scan_policy_drift(tenant_key)

@router.get("/federation/evidence")
async def get_federated_evidence(tenant_key: str | None = None, db: AsyncSession = Depends(get_db)):
    """Centralized audit trail of evidence hashes across the federation."""
    svc = UIRepairService(db)
    return await svc.get_federated_evidence(tenant_key)

@router.get("/finops/costs", response_model=List[UICostEventSchema])
async def list_cost_events(
    project_key: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    """List recent cost events with attribution."""
    svc = UIRepairService(db)
    return await svc.list_cost_events(project_key)

@router.get("/finops/budget/{project_key}", response_model=UIBudgetPolicySchema | None)
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
    project_key: str | None = None,
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

@router.get("/finops/forecast/{project_key}", response_model=UICapacityForecastSchema | None)
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
    project_key: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    """List cost-saving recommendations."""
    svc = UIRepairService(db)
    return await svc.list_finops_recommendations(project_key)

@router.post("/finops/recommendations/{rec_id}/status", response_model=UIFinOpsRecommendationSchema)
async def update_recommendation_status(
    rec_id: str, 
    status: str = Query(..., pattern="^(PENDING|APPLIED|DISMISSED)$"),
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
    project_key: str | None = None,
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
    project_key: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    """Audit log of policy evaluations."""
    stmt = select(UIPolicyEvaluation)
    if project_key:
        stmt = stmt.where(UIPolicyEvaluation.project_key == project_key)
    stmt = stmt.order_by(UIPolicyEvaluation.evaluated_at.desc())
    res = await db.execute(stmt)
    return list(res.scalars().all())

@router.get("/governance/overrides", response_model=List[UIAutonomousOverrideSchema])
async def list_policy_overrides(
    tenant_key: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    """Audit log of manual autonomous governance overrides."""
    stmt = select(UIAutonomousOverride)
    if tenant_key:
        stmt = stmt.where(UIAutonomousOverride.tenant_key == tenant_key)
    stmt = stmt.order_by(UIAutonomousOverride.created_at.desc())
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

@router.get("/governance/compliance-findings", response_model=List[UISecurityPostureFindingSchema])
async def list_compliance_findings(
    project_key: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    """Lists compliance violations found in the ecosystem."""
    svc = UIRepairService(db)
    return await svc.get_compliance_findings(project_key)

@router.get("/governance/proposals", response_model=List[UIPolicyProposalSchema])
async def list_policy_proposals(
    project_key: str | None = None,
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
    project_key: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    """Lists detected policy conflicts."""
    svc = UIRepairService(db)
    return await svc.list_policy_conflicts(project_key)

@router.post("/governance/simulate")
async def simulate_policy(
    rule_definition: Dict[str, Any] = Body(...),
    project_key: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    """Simulates a policy rule against historical evaluations."""
    from .policy_simulator import PolicySimulator
    simulator = PolicySimulator(db)
    return await simulator.simulate_rule(rule_definition, project_key)

# --- Phase 21: Security Posture & Compliance ---

@router.get("/security/posture", response_model=UISecurityPostureScoreSchema)
async def get_latest_security_posture(
    tenant_key: str | None = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Gets the latest security posture score and level."""
    from .security_posture_manager import SecurityPostureManager
    from libs.db.models.ui_repair_models import UISecurityPostureScore
    
    stmt = select(UISecurityPostureScore).where(UISecurityPostureScore.tenant_key == tenant_key).order_by(UISecurityPostureScore.created_at.desc())
    score = (await db.execute(stmt)).scalar_one_or_none()
    
    if not score:
        manager = SecurityPostureManager(db)
        score = await manager.run_full_scan(tenant_key)
        
    return score

@router.get("/security/controls", response_model=List[UIComplianceControlSchema])
async def list_compliance_controls(db: AsyncSession = Depends(get_db)):
    """Lists all defined compliance controls."""
    from libs.db.models.ui_repair_models import UIComplianceControl
    
    stmt = select(UIComplianceControl)
    controls = (await db.execute(stmt)).scalars().all()
    
    if not controls:
        from .security_posture_manager import SecurityPostureManager
        manager = SecurityPostureManager(db)
        await manager.initialize_controls()
        controls = (await db.execute(stmt)).scalars().all()
        
    return controls

@router.get("/security/findings", response_model=List[UISecurityPostureFindingSchema])
async def list_compliance_findings(
    tenant_key: str | None = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Lists recent compliance findings."""
    from libs.db.models.ui_repair_models import UISecurityPostureFinding
    
    stmt = select(UISecurityPostureFinding).where(UISecurityPostureFinding.tenant_key == tenant_key).order_by(UISecurityPostureFinding.created_at.desc())
    return (await db.execute(stmt)).scalars().all()

@router.post("/security/scan", response_model=UISecurityPostureScoreSchema)
async def trigger_security_scan(
    tenant_key: str | None = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Triggers an immediate platform security posture scan."""
    from .security_posture_manager import SecurityPostureManager
    manager = SecurityPostureManager(db)
    return await manager.run_full_scan(tenant_key)

@router.post("/security/certify", response_model=UISecurityCertificationSchema)
async def generate_compliance_certification(
    tenant_key: str | None = Query(None),
    operator_name: str = Query("System"),
    db: AsyncSession = Depends(get_db)
):
    """Generates a new Continuous Compliance Certification Report."""
    from .security_posture_manager import SecurityPostureManager
    manager = SecurityPostureManager(db)
    return await manager.certify_compliance(tenant_key, operator_name)

@router.get("/security/certifications", response_model=List[UISecurityCertificationSchema])
async def list_certifications(
    tenant_key: str | None = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Lists historical certification records."""
    from libs.db.models.ui_repair_models import UISecurityCertification
    
    stmt = select(UISecurityCertification).where(UISecurityCertification.tenant_key == tenant_key).order_by(UISecurityCertification.created_at.desc())
    return (await db.execute(stmt)).scalars().all()

# --- Phase 22: Security Remediation & Compliance Auto-Fix ---

@router.post("/security/remediation/plan/{finding_id}", response_model=Dict[str, Any])
async def orchestrate_security_remediation(
    finding_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Triggers the full remediation lifecycle for a security finding."""
    service = UIRepairService(db)
    return await service.orchestrate_security_remediation(finding_id)

@router.get("/security/remediation/plans", response_model=List[UISecurityRemediationPlanSchema])
async def list_remediation_plans(
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Lists active remediation plans."""
    service = UIRepairService(db)
    return await service.list_remediation_plans(status)

@router.get("/security/remediation/attempts", response_model=List[UISecurityAutoFixAttemptSchema])
async def list_autofix_attempts(
    finding_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Lists auto-fix attempts."""
    service = UIRepairService(db)
    return await service.list_autofix_attempts(finding_id)

@router.get("/security/remediation/summary", response_model=Dict[str, Any])
async def get_remediation_summary(
    db: AsyncSession = Depends(get_db)
):
    """Returns aggregated metrics for the remediation dashboard."""
    service = UIRepairService(db)
    return await service.get_remediation_summary()

@router.get("/security/remediation/risks", response_model=List[Dict[str, Any]])
async def list_residual_risks(
    db: AsyncSession = Depends(get_db)
):
    """Lists unresolved security risks."""
    service = UIRepairService(db)
    return await service.list_residual_risks()

@router.post("/security/remediation/finalize/{attempt_id}", response_model=Dict[str, Any])
async def finalize_security_remediation(
    attempt_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Finalizes and verifies a security remediation attempt."""
    service = UIRepairService(db)
    return await service.finalize_security_remediation(attempt_id)

# --- Phase 23: Autonomous Threat Modeling + Attack Path Simulation ---

@router.get("/security/threat/assets", response_model=List[UIAttackSurfaceAssetSchema])
async def get_attack_surface_assets(
    tenant_key: str | None = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Lists discovered attack surface assets."""
    service = UIRepairService(db)
    return await service.get_attack_surface_assets(tenant_key)

@router.post("/security/threat/inventory/scan", response_model=List[UIAttackSurfaceAssetSchema])
async def trigger_attack_surface_scan(
    tenant_key: str | None = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Triggers a new attack surface discovery scan."""
    service = UIRepairService(db)
    return await service.trigger_attack_surface_scan(tenant_key)

@router.post("/security/threat/models/generate", response_model=UIThreatModelSchema)
async def generate_threat_model(
    scope: str = Query("SYSTEM"),
    tenant_key: str | None = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Triggers autonomous threat model generation."""
    service = UIRepairService(db)
    return await service.generate_threat_model(scope, tenant_key)

@router.get("/security/threat/models", response_model=List[UIThreatModelSchema])
async def list_threat_models(db: AsyncSession = Depends(get_db)):
    """Lists all generated threat models."""
    service = UIRepairService(db)
    return await service.list_threat_models()

@router.get("/security/threat/models/{model_id}", response_model=UIThreatModelSchema)
async def get_threat_model_detail(model_id: UUID, db: AsyncSession = Depends(get_db)):
    """Fetches details for a specific threat model."""
    from libs.db.models.ui_repair_models import UIThreatModel
    stmt = select(UIThreatModel).where(UIThreatModel.id == model_id)
    res = await db.execute(stmt)
    model = res.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Threat model not found")
    return model

@router.get("/security/threat/attack-paths", response_model=List[UIAttackPathSchema])
async def list_attack_paths(
    threat_model_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Lists identified attack paths."""
    service = UIRepairService(db)
    return await service.list_attack_paths(threat_model_id)

@router.post("/security/threat/attack-paths/{path_id}/simulate", response_model=UIAttackSimulationRunSchema)
async def simulate_attack_path(
    path_id: UUID,
    mode: str = Query("DRY_RUN"),
    db: AsyncSession = Depends(get_db)
):
    """Triggers a controlled simulation of a specific attack path."""
    service = UIRepairService(db)
    return await service.simulate_attack_path(path_id, mode)

@router.get("/security/threat/simulations", response_model=List[UIAttackSimulationRunSchema])
async def list_attack_simulations(db: AsyncSession = Depends(get_db)):
    """Lists all attack simulation runs."""
    service = UIRepairService(db)
    return await service.list_attack_simulations()

@router.get("/security/threat/mitigations", response_model=List[UIThreatMitigationSchema])
async def list_threat_mitigations(db: AsyncSession = Depends(get_db)):
    """Lists recommended security mitigations."""
    service = UIRepairService(db)
    return await service.list_threat_mitigations()

@router.get("/security/threat/summary", response_model=UIThreatSummarySchema)
async def get_threat_summary(db: AsyncSession = Depends(get_db)):
    """Returns aggregated threat modeling metrics."""
    service = UIRepairService(db)
    return await service.get_threat_summary()

@router.post("/security/threat/report/generate", response_model=Dict[str, Any])
async def generate_threat_report(db: AsyncSession = Depends(get_db)):
    """Generates the latest threat landscape report."""
    from .threat_model_reporter import ThreatModelReporter
    reporter = ThreatModelReporter(db)
    return await reporter.generate_latest_report()

# --- Phase 24: Autonomous Red Teaming + Adversarial Drift Detection ---

@router.get("/security/red-team/overview", response_model=UIRedTeamOverviewSchema)
async def get_red_team_overview(db: AsyncSession = Depends(get_db)):
    """Retrieves high-level metrics for Red Team operations."""
    service = UIRepairService(db)
    return await service.get_red_team_overview()

@router.get("/security/red-team/scenarios", response_model=List[UIRedTeamScenarioSchema])
async def list_red_team_scenarios(db: AsyncSession = Depends(get_db)):
    """Lists available adversarial attack scenarios."""
    service = UIRepairService(db)
    return await service.list_red_team_scenarios()

@router.post("/security/red-team/scenarios/generate", response_model=List[UIRedTeamScenarioSchema])
async def generate_red_team_scenarios(db: AsyncSession = Depends(get_db)):
    """Generates Red Team scenarios from attack paths and standards."""
    service = UIRepairService(db)
    return await service.generate_red_team_scenarios()

@router.post("/security/red-team/scenarios/{scenario_id}/run", response_model=UIRedTeamRunSchema)
async def run_red_team_scenario(scenario_id: UUID, db: AsyncSession = Depends(get_db)):
    """Triggers an autonomous Red Team operation for a scenario."""
    service = UIRepairService(db)
    return await service.run_red_team_scenario(scenario_id)

@router.post("/security/red-team/run-suite", response_model=Dict[str, Any])
async def run_red_team_suite(db: AsyncSession = Depends(get_db)):
    """Runs all enabled Red Team scenarios."""
    service = UIRepairService(db)
    return await service.run_red_team_suite()

@router.get("/security/red-team/runs", response_model=List[UIRedTeamRunSchema])
async def list_red_team_runs(db: AsyncSession = Depends(get_db)):
    """Lists recent Red Team runs."""
    service = UIRepairService(db)
    return await service.list_red_team_runs()

@router.get("/security/red-team/runs/{run_id}", response_model=UIRedTeamRunSchema)
async def get_red_team_run(run_id: UUID, db: AsyncSession = Depends(get_db)):
    """Retrieves details of a specific Red Team run."""
    service = UIRepairService(db)
    return await service.get_red_team_run(run_id)

@router.get("/security/red-team/probes", response_model=List[UIAdversarialProbeSchema])
async def list_red_team_probes(run_id: UUID | None = None, db: AsyncSession = Depends(get_db)):
    """Lists adversarial probes executed during runs."""
    service = UIRepairService(db)
    return await service.list_red_team_probes(run_id)

@router.get("/security/red-team/drift-events", response_model=List[UIAdversarialDriftEventSchema])
async def list_red_team_drift_events(db: AsyncSession = Depends(get_db)):
    """Lists security behavior drift events."""
    service = UIRepairService(db)
    return await service.list_red_team_drift_events()

@router.get("/security/red-team/findings", response_model=List[UIRedTeamFindingSchema])
async def list_red_team_findings(db: AsyncSession = Depends(get_db)):
    """Lists security findings from Red Team operations."""
    service = UIRepairService(db)
    return await service.list_red_team_findings()

@router.post("/security/red-team/report/generate", response_model=UIRedTeamReportSchema)
async def generate_red_team_report(db: AsyncSession = Depends(get_db)):
    """Generates an executive Red Team audit report."""
    service = UIRepairService(db)
    return await service.generate_red_team_report()

@router.get("/security/red-team/report/latest", response_model=UIRedTeamReportSchema | None)
async def get_latest_red_team_report(db: AsyncSession = Depends(get_db)):
    """Retrieves the most recent Red Team audit report."""
    service = UIRepairService(db)
    return await service.get_latest_red_team_report()

# --- Phase 25: Autonomous Defense Optimization ---

@router.get("/security/defense/overview", response_model=UIDefenseOverviewSchema)
async def get_defense_overview(db: AsyncSession = Depends(get_db)):
    """Aggregated defense posture summary for the shield dashboard."""
    service = UIRepairService(db)
    return await service.get_defense_overview()

@router.post("/security/defense/optimization/cycle", response_model=List[UIGuardrailTuningProposalSchema])
async def trigger_defense_optimization_cycle(db: AsyncSession = Depends(get_db)):
    """Triggers an autonomous defense optimization cycle (Findings -> Patterns -> Proposals)."""
    service = UIRepairService(db)
    return await service.optimization_engine.run_optimization_cycle()

@router.get("/security/defense/proposals", response_model=List[UIGuardrailTuningProposalSchema])
async def list_tuning_proposals(db: AsyncSession = Depends(get_db)):
    """Lists all generated guardrail tuning proposals."""
    service = UIRepairService(db)
    return await service.tuning_service.get_all_proposals()

@router.get("/security/defense/proposals/{proposal_id}", response_model=UIGuardrailTuningProposalSchema)
async def get_tuning_proposal(proposal_id: UUID, db: AsyncSession = Depends(get_db)):
    """Retrieves details for a specific tuning proposal."""
    service = UIRepairService(db)
    proposal = await service.tuning_service.get_proposal(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return proposal

@router.post("/security/defense/proposals/{proposal_id}/promote", response_model=UIGuardrailTuningProposalSchema)
async def promote_tuning_proposal(proposal_id: UUID, db: AsyncSession = Depends(get_db)):
    """Promotes a proposal through verification stages (Regression -> Canary -> Gov)."""
    service = UIRepairService(db)
    proposal = await service.optimization_engine.promote_proposal(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return proposal

@router.post("/security/defense/proposals/{proposal_id}/approve", response_model=UIGuardrailTuningProposalSchema)
async def approve_tuning_proposal(proposal_id: UUID, db: AsyncSession = Depends(get_db)):
    """Manually approves a proposal for application (Operator Gate)."""
    service = UIRepairService(db)
    proposal = await service.tuning_service.approve_proposal(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return proposal

@router.post("/security/defense/proposals/{proposal_id}/apply", response_model=UIGuardrailTuningProposalSchema)
async def apply_tuning_proposal(proposal_id: UUID, db: AsyncSession = Depends(get_db)):
    """Executes an approved tuning proposal on the live policy engine."""
    service = UIRepairService(db)
    try:
        return await service.optimization_engine.apply_proposal(proposal_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Phase 28: Auto-Remediation Observability + Multi-Agent Patch Negotiation ---

@router.get("/security/autopatch/{execution_id}/traces", response_model=List[AutoPatchTraceSchema])
async def get_execution_traces(execution_id: UUID, db: AsyncSession = Depends(get_db)):
    """Phase 28: Gets observability traces for a specific execution."""
    service = UIRepairService(db)
    return await service.get_execution_traces(execution_id)

@router.get("/security/autopatch/{execution_id}/negotiation", response_model=PatchNegotiationSessionSchema | None)
async def get_negotiation_session(execution_id: UUID, db: AsyncSession = Depends(get_db)):
    """Phase 28: Gets the negotiation session for an execution."""
    service = UIRepairService(db)
    return await service.get_negotiation_session(execution_id)

@router.get("/security/autopatch/negotiation/{session_id}/debate", response_model=List[PatchDebateTurnSchema])
async def get_debate_turns(session_id: UUID, db: AsyncSession = Depends(get_db)):
    """Phase 28: Gets the debate turns for a negotiation session."""
    service = UIRepairService(db)
    return await service.get_debate_turns(session_id)

@router.get("/security/autopatch/candidate/{candidate_id}/scores", response_model=PatchCandidateScoreSchema | None)
async def get_candidate_scores(candidate_id: UUID, db: AsyncSession = Depends(get_db)):
    """Phase 28: Gets the multi-dimensional scores for a candidate."""
    service = UIRepairService(db)
    return await service.get_candidate_scores(candidate_id)

@router.post("/security/autopatch/negotiation/start")
async def start_negotiation(req: NegotiationStartRequest, db: AsyncSession = Depends(get_db)):
    """Phase 28: Manually triggers a negotiation session."""
    service = UIRepairService(db)
    return await service.start_negotiation_session(req.execution_id, req.agents)

@router.get("/security/defense/patterns", response_model=List[UIDefensivePatternSchema])
async def list_defensive_patterns(db: AsyncSession = Depends(get_db)):
    """Lists reusable defensive patterns synthesized from adversarial findings."""
    service = UIRepairService(db)
    return await service.tuning_service.get_patterns()

@router.get("/security/defense/report/latest", response_model=UIDefenseOptimizationReportSchema | None)
async def get_latest_defense_report(db: AsyncSession = Depends(get_db)):
    """Retrieves the latest executive defense optimization report."""
    service = UIRepairService(db)
    return await service.defense_reporter.get_latest_report()

@router.post("/security/defense/report/generate", response_model=UIDefenseOptimizationReportSchema)
async def generate_defense_report(db: AsyncSession = Depends(get_db)):
    """Generates a new executive defense optimization report."""
    service = UIRepairService(db)
    return await service.defense_reporter.generate_latest_report()

# --- Phase 26: Incident War Room & Executive Risk ---

@router.get("/war-rooms", response_model=List[UIIncidentWarRoomSchema])
async def list_war_rooms(status: str | None = None, db: AsyncSession = Depends(get_db)):
    svc = UIRepairService(db)
    return await svc.list_war_rooms(status)

@router.get("/war-rooms/{war_room_id}", response_model=UIIncidentWarRoomSchema)
async def get_war_room(war_room_id: UUID, db: AsyncSession = Depends(get_db)):
    svc = UIRepairService(db)
    wr = await svc.get_war_room(war_room_id)
    if not wr:
        raise HTTPException(status_code=404, detail="War Room not found")
    return wr

@router.get("/war-rooms/{war_room_id}/timeline", response_model=List[UIIncidentTimelineEventSchema])
async def get_war_room_timeline(war_room_id: UUID, db: AsyncSession = Depends(get_db)):
    svc = UIRepairService(db)
    return await svc.get_war_room_timeline(war_room_id)

@router.get("/war-rooms/{war_room_id}/actions", response_model=List[UIIncidentActionItemSchema])
async def get_war_room_actions(war_room_id: UUID, db: AsyncSession = Depends(get_db)):
    svc = UIRepairService(db)
    return await svc.get_war_room_actions(war_room_id)

@router.post("/war-rooms/{war_room_id}/actions", response_model=UIIncidentActionItemSchema)
async def add_war_room_action(war_room_id: UUID, data: UIIncidentActionItemCreate, db: AsyncSession = Depends(get_db)):
    svc = UIRepairService(db)
    return await svc.add_war_room_action(
        war_room_id, data.action_type, data.title, data.owner, data.due_at
    )

@router.post("/war-rooms/{war_room_id}/resolve")
async def resolve_war_room(war_room_id: UUID, data: WarRoomResolveRequest, db: AsyncSession = Depends(get_db)):
    svc = UIRepairService(db)
    await svc.resolve_war_room(war_room_id, data.rationale, data.actor)
    return {"status": "success"}

@router.get("/risk/overview", response_model=ExecutiveRiskOverview)
async def get_executive_risk_overview(db: AsyncSession = Depends(get_db)):
    svc = UIRepairService(db)
    return await svc.get_executive_risk_overview()

@router.get("/risk/reports", response_model=List[UIExecutiveRiskReportSchema])
async def list_executive_risk_reports(limit: int = 10, db: AsyncSession = Depends(get_db)):
    svc = UIRepairService(db)
    return await svc.list_executive_risk_reports(limit)

@router.post("/risk/reports/generate", response_model=UIExecutiveRiskReportSchema)
async def generate_executive_risk_report(report_name: str = Query(...), db: AsyncSession = Depends(get_db)):
    service = UIRepairService(db)
    return await service.generate_executive_risk_report(report_name)

# --- Phase 27: Autonomous Remediation Execution (Auto-Patch v2) ---

@router.get("/security/autopatch/executions", response_model=List[AutoPatchExecutionSchema])
async def list_autopatch_executions(limit: int = Query(20), db: AsyncSession = Depends(get_db)):
    """Lists recent Auto-Patch v2 executions."""
    service = UIRepairService(db)
    return await service.list_autopatch_executions(limit)

@router.post("/security/autopatch/executions/start", response_model=AutoPatchExecutionSchema)
async def start_autopatch_execution(req: AutoPatchStartRequest, db: AsyncSession = Depends(get_db)):
    """Starts a new Auto-Patch v2 execution from a source (e.g. War Room action)."""
    service = UIRepairService(db)
    return await service.start_autopatch_execution(
        source_type=req.source_type,
        source_id=req.source_id,
        war_room_id=req.war_room_id,
        action_item_id=req.action_item_id,
        remediation_plan_id=req.remediation_plan_id,
        risk_level=req.risk_level or "MEDIUM"
    )

@router.get("/security/autopatch/executions/{execution_id}", response_model=AutoPatchExecutionSchema)
async def get_autopatch_execution(execution_id: UUID, db: AsyncSession = Depends(get_db)):
    """Retrieves details of a specific Auto-Patch execution."""
    service = UIRepairService(db)
    return await service.get_autopatch_execution(execution_id)

@router.post("/security/autopatch/executions/{execution_id}/preflight", response_model=Dict[str, Any])
async def run_autopatch_preflight(execution_id: UUID, db: AsyncSession = Depends(get_db)):
    """Triggers safety preflight checks for an execution."""
    service = UIRepairService(db)
    return await service.run_autopatch_preflight(execution_id)

@router.post("/security/autopatch/executions/{execution_id}/generate-patch", response_model=Dict[str, Any])
async def run_autopatch_generate(execution_id: UUID, db: AsyncSession = Depends(get_db)):
    """Triggers patch generation and planning."""
    service = UIRepairService(db)
    return await service.run_autopatch_generate(execution_id)

@router.post("/security/autopatch/executions/{execution_id}/verify", response_model=VerificationRunV2Schema)
async def run_autopatch_verify(execution_id: UUID, db: AsyncSession = Depends(get_db)):
    """Runs the full verification suite for a generated patch."""
    service = UIRepairService(db)
    return await service.run_autopatch_verify(execution_id)

@router.post("/security/autopatch/executions/{execution_id}/apply", response_model=PostApplyValidationSchema)
async def run_autopatch_apply(execution_id: UUID, req: AutoPatchActionRequest, db: AsyncSession = Depends(get_db)):
    """Applies the verified patch with operator rationale."""
    service = UIRepairService(db)
    return await service.run_autopatch_apply(execution_id, req.rationale, req.actor)

@router.post("/security/autopatch/executions/{execution_id}/rollback", response_model=RollbackExecutionSchema)
async def run_autopatch_rollback(execution_id: UUID, req: AutoPatchActionRequest, db: AsyncSession = Depends(get_db)):
    """Manually triggers a rollback for an execution."""
    service = UIRepairService(db)
    return await service.run_autopatch_rollback(execution_id, req.rationale)

@router.get("/security/autopatch/candidates", response_model=List[PatchCandidateSchema])
async def list_patch_candidates(execution_id: UUID = Query(...), db: AsyncSession = Depends(get_db)):
    """Lists all candidates generated for an execution."""
    service = UIRepairService(db)
    return await service.list_patch_candidates(execution_id)

# --- Phase 29: Knowledge Graph & Causal Memory Endpoints ---

@router.post("/knowledge/rebuild", response_model=Dict[str, int], tags=["Knowledge"])
async def rebuild_knowledge_graph(db: AsyncSession = Depends(get_db)):
    """Triggers a full rebuild of the Knowledge Graph from system events."""
    builder = KnowledgeGraphBuilder(db)
    return await builder.rebuild_graph()

@router.get("/knowledge/overview", response_model=UIKnowledgeGraphOverviewSchema, tags=["Knowledge"])
async def get_knowledge_overview(db: AsyncSession = Depends(get_db)):
    """Returns an overview of the knowledge graph statistics."""
    from libs.db.models.ui_repair_models import UIKnowledgeNode
    from sqlalchemy import func
    node_count = (await db.execute(select(func.count(UIKnowledgeNode.id)))).scalar() or 0
    if node_count == 0:
        from services.ui_repair.baseline_bootstrap import UIRepairBaselineBootstrapper
        bootstrapper = UIRepairBaselineBootstrapper(db)
        await bootstrapper.ensure_baseline()
    builder = KnowledgeGraphBuilder(db)
    return await builder.get_graph_overview()

@router.get("/knowledge/nodes", response_model=List[UIKnowledgeNodeSchema], tags=["Knowledge"])
async def list_knowledge_nodes(
    node_type: str | None = None,
    severity: str | None = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Lists knowledge nodes with optional filtering."""
    from libs.db.models.ui_repair_models import UIKnowledgeNode
    stmt = select(UIKnowledgeNode)
    if node_type:
        stmt = stmt.where(UIKnowledgeNode.node_type == node_type)
    if severity:
        stmt = stmt.where(UIKnowledgeNode.severity == severity)
    stmt = stmt.limit(limit).order_by(UIKnowledgeNode.created_at.desc())
    res = await db.execute(stmt)
    results = res.scalars().all()
    if not results and not node_type and not severity:
        from services.ui_repair.baseline_bootstrap import UIRepairBaselineBootstrapper
        bootstrapper = UIRepairBaselineBootstrapper(db)
        await bootstrapper.ensure_baseline()
        res = await db.execute(stmt)
        results = res.scalars().all()
    # Mapping to schema
    nodes = []
    for n in results:
        nodes.append(UIKnowledgeNodeSchema(
            id=n.id, node_key=n.node_key, node_type=n.node_type,
            source_type=n.source_type, source_id=n.source_id,
            tenant_key=n.tenant_key, project_key=n.project_key, cluster_key=n.cluster_key,
            title=n.title, summary=n.summary, severity=n.severity,
            confidence=n.confidence, metadata_json=n.metadata_json,
            created_at=n.created_at, updated_at=n.updated_at
        ))
    return nodes

@router.get("/knowledge/edges", response_model=List[UIKnowledgeEdgeSchema], tags=["Knowledge"])
async def list_knowledge_edges(
    source_node_key: str | None = None,
    edge_type: str | None = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Lists knowledge edges with optional filtering."""
    from libs.db.models.ui_repair_models import UIKnowledgeEdge
    stmt = select(UIKnowledgeEdge)
    if source_node_key:
        stmt = stmt.where(UIKnowledgeEdge.source_node_key == source_node_key)
    if edge_type:
        stmt = stmt.where(UIKnowledgeEdge.edge_type == edge_type)
    stmt = stmt.limit(limit)
    res = await db.execute(stmt)
    results = res.scalars().all()
    if not results and not source_node_key and not edge_type:
        from services.ui_repair.baseline_bootstrap import UIRepairBaselineBootstrapper
        bootstrapper = UIRepairBaselineBootstrapper(db)
        await bootstrapper.ensure_baseline()
        res = await db.execute(stmt)
        results = res.scalars().all()
    edges = []
    for e in results:
        edges.append(UIKnowledgeEdgeSchema(
            id=e.id, source_node_key=e.source_node_key, target_node_key=e.target_node_key,
            edge_type=e.edge_type, confidence=e.confidence,
            evidence_refs_json=e.evidence_refs_json, metadata_json=e.metadata_json,
            created_at=e.created_at
        ))
    return edges

@router.get("/knowledge/predictions", response_model=List[UIRiskPredictionSchema], tags=["Knowledge"])
async def list_risk_predictions(db: AsyncSession = Depends(get_db)):
    """Lists all active risk predictions."""
    from libs.db.models.ui_repair_models import UIRiskPrediction
    stmt = select(UIRiskPrediction).where(UIRiskPrediction.status == "ACTIVE")
    res = await db.execute(stmt)
    predictions = []
    for p in res.scalars().all():
        predictions.append(UIRiskPredictionSchema(
            id=p.id, prediction_key=p.prediction_key, target_type=p.target_type,
            target_key=p.target_key, risk_type=p.risk_type, probability=p.probability,
            severity=p.severity, predicted_window=p.predicted_window,
            contributing_factors_json=p.contributing_factors_json,
            recommended_prevention=p.recommended_prevention, status=p.status,
            created_at=p.created_at
        ))
    return predictions

@router.post("/knowledge/predictions/generate", response_model=List[UIRiskPredictionSchema], tags=["Knowledge"])
async def generate_risk_predictions(db: AsyncSession = Depends(get_db)):
    """Triggers the risk prediction engine to generate new insights."""
    engine = RiskPredictionEngine(db)
    preds = await engine.generate_predictions()
    results = []
    for p in preds:
        results.append(UIRiskPredictionSchema(
            id=p.id, prediction_key=p.prediction_key, target_type=p.target_type,
            target_key=p.target_key, risk_type=p.risk_type, probability=p.probability,
            severity=p.severity, predicted_window=p.predicted_window,
            contributing_factors_json=p.contributing_factors_json,
            recommended_prevention=p.recommended_prevention, status=p.status,
            created_at=p.created_at
        ))
    return results

@router.post("/knowledge/similar-cases", response_model=List[UISimilarCaseMatchSchema], tags=["Knowledge"])
async def find_similar_cases(request: SimilarCaseRequest, db: AsyncSession = Depends(get_db)):
    """Finds historical cases similar to the provided one."""
    from libs.db.models.ui_repair_models import UISimilarCaseMatch
    # Simplified mock search for now
    stmt = select(UISimilarCaseMatch).where(UISimilarCaseMatch.query_source_id == request.source_id)
    res = await db.execute(stmt)
    matches = []
    for m in res.scalars().all():
        matches.append(UISimilarCaseMatchSchema(
            id=m.id, query_source_type=m.query_source_type, query_source_id=m.query_source_id,
            matched_source_type=m.matched_source_type, matched_source_id=m.matched_source_id,
            similarity_score=m.similarity_score, matched_features_json=m.matched_features_json,
            recommended_action=m.recommended_action, confidence=m.confidence,
            created_at=m.created_at
        ))
    return matches

# --- Phase 30: Final Integration + Production Hardening + Release Lock Endpoints ---

@router.get("/final/readiness", response_model=Dict[str, Any], tags=["Final Release"])
async def get_release_readiness(db: AsyncSession = Depends(get_db)):
    """Provides a summary of release readiness across all categories."""
    checker = ReleaseReadinessChecker(db)
    return await checker.get_readiness_summary()

@router.post("/final/readiness/check", response_model=List[UIReleaseReadinessCheckSchema], tags=["Final Release"])
async def run_readiness_check(db: AsyncSession = Depends(get_db)):
    """Triggers a full system readiness check."""
    checker = ReleaseReadinessChecker(db)
    checks = await checker.check_readiness()
    return [UIReleaseReadinessCheckSchema.model_validate(c) for c in checks]

@router.get("/final/integration-audits", response_model=List[UIFinalIntegrationAuditSchema], tags=["Final Release"])
async def list_integration_audits(db: AsyncSession = Depends(get_db)):
    """Lists all historical integration audits."""
    from libs.db.models.ui_repair_models import UIFinalIntegrationAudit
    stmt = select(UIFinalIntegrationAudit).order_by(UIFinalIntegrationAudit.created_at.desc())
    res = await db.execute(stmt)
    return [UIFinalIntegrationAuditSchema.model_validate(a) for a in res.scalars().all()]

@router.post("/final/integration-audit/run", response_model=UIFinalIntegrationAuditSchema, tags=["Final Release"])
async def run_integration_audit(db: AsyncSession = Depends(get_db)):
    """Triggers a new system-wide integration audit."""
    auditor = FinalIntegrationAuditor(db)
    audit = await auditor.run_audit()
    return UIFinalIntegrationAuditSchema.model_validate(audit)

@router.post("/final/smoke-test/run", response_model=List[UISmokeTestResultSchema], tags=["Final Release"])
async def run_smoke_tests(db: AsyncSession = Depends(get_db)):
    """Executes core system smoke tests."""
    runner = SystemSmokeTestRunner(db)
    return await runner.run_smoke_tests()

@router.post("/final/audit-pack/generate", response_model=UIFinalAuditPackSchema, tags=["Final Release"])
async def generate_audit_pack(version: str = Query("1.0.0"), db: AsyncSession = Depends(get_db)):
    """Generates the final audit package for a release."""
    generator = FinalAuditPackGenerator(db)
    pack = await generator.generate_pack(version)
    return UIFinalAuditPackSchema.model_validate(pack)

@router.get("/final/audit-pack/latest", response_model=UIFinalAuditPackSchema | None, tags=["Final Release"])
async def get_latest_audit_pack(db: AsyncSession = Depends(get_db)):
    """Fetches the most recently generated audit pack."""
    generator = FinalAuditPackGenerator(db)
    pack = await generator.get_latest_pack()
    return UIFinalAuditPackSchema.model_validate(pack) if pack else None

@router.post("/final/release-lock", response_model=UIReleaseLockSchema, tags=["Final Release"])
async def create_release_lock(version: str = Body(..., embed=True), locked_by: str = Body(..., embed=True), audit_pack_id: UUID = Body(..., embed=True), db: AsyncSession = Depends(get_db)):
    """Creates a final release lock. Only allowed if readiness check is passed."""
    readiness_checker = ReleaseReadinessChecker(db)
    summary = await readiness_checker.get_readiness_summary()
    
    if summary["status"] == ReleaseStatus.BLOCKED:
        raise HTTPException(status_code=400, detail=f"Cannot seal release: Blockers detected. {summary['blockers']}")
    
    if summary["score"] < 90:
        raise HTTPException(status_code=400, detail=f"Cannot seal release: Readiness score too low ({summary['score']}%). Minimum 90% required.")
        
    manager = ReleaseLockManager(db)
    lock = await manager.create_release_lock(version, locked_by, audit_pack_id)
    return UIReleaseLockSchema.model_validate(lock)

@router.get("/final/release-lock/latest", response_model=UIReleaseLockSchema | None, tags=["Final Release"])
async def get_latest_release_lock(db: AsyncSession = Depends(get_db)):
    """Fetches the latest release lock."""
    manager = ReleaseLockManager(db)
    lock = await manager.get_latest_lock()
    return UIReleaseLockSchema.model_validate(lock) if lock else None

@router.get("/final/phase-completion-matrix", response_model=List[UIPhaseCompletionSchema], tags=["Final Release"])
async def get_phase_completion_matrix(db: AsyncSession = Depends(get_db)):
    """Returns a summary of completion status for all 30 phases."""
    service = UIRepairService(db)
    phases = await service.get_release_phase_completion_matrix()
    return [UIPhaseCompletionSchema.model_validate(phase) for phase in phases]

@router.get("/final/residual-risks", response_model=List[UIResidualRiskSchema], tags=["Final Release"])
async def get_residual_risks(db: AsyncSession = Depends(get_db)):
    """Lists data-driven residual risks for the current release candidate."""
    service = UIRepairService(db)
    risks = await service.get_residual_release_risks()
    return [UIResidualRiskSchema.model_validate(risk) for risk in risks]

@router.post("/final/residual-risks/{risk_id}/sign-off", response_model=UIResidualRiskSchema, tags=["Final Release"])
async def sign_off_residual_risk(
    risk_id: str,
    operator: str = Body(..., embed=True),
    rationale: Optional[str] = Body(default=None, embed=True),
    db: AsyncSession = Depends(get_db),
):
    """Persists operator acceptance for a residual risk."""
    service = UIRepairService(db)
    try:
        risk = await service.accept_residual_risk(risk_id, operator, rationale)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return UIResidualRiskSchema.model_validate(risk)
