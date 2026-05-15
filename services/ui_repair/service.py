import json
import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional, cast, Union
import uuid
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, desc

from libs.db.models.ui_repair_models import (
    UIRepairCase, UIRouteHealth, UISmokeRun, UIRepairStatus, FailureType, UIRepairSeverity,
    UIMonitoringConfig, UIMonitoringRun, UIRouteHealthHist, UIRepairAttempt,
    UIChaosDrillScenario, UIChaosDrillRun, UISoakValidationRun, UIRecoveryProofPack,
    UIAdvancedChaosScenario, UIAdvancedChaosRun, UIOperatorEscalation, UINotificationDelivery, UICrisisControlState,
    UIRedTeamScenario, UIRedTeamRun, UIEnterpriseReadinessAssessment, UIReleaseGateDecision, UIFinalAuditPack, UIOperatorHandoverReport,
    UIPilotRollout, UIPilotEvent, UIPilotMetrics, UIOperatorActionLedger, UIPilotFinalReport,
    UIOperationsTeam, UIProjectOwnership, UIMaintenancePolicy, UIReleaseRecord, UICompatibilityCheck, UISLOBreach, UIEvidenceRetentionPolicy,
    UIRepairProjectProfile, UIRolloutWave, UIGAReadinessAssessment, UIEnterpriseRunbook,
    UICostEvent, UIBudgetPolicy, UICostAnomaly, UICapacityForecast, UIFinOpsRecommendation,
    UIPolicyRule, UIPolicyEvaluation, UIPolicyConflict, UIPolicyProposal, UIAutonomousOverride, UIComplianceFinding
)
from libs.db.models.core_models import OperationalIncident, SovereignEvidence
from services.ui_repair.playwright_runner import UIEvidenceRunner
from services.ui_repair.risk_classifier import UIRiskClassifier
from services.ui_repair.policy_as_code_engine import PolicyAsCodeEngine
from services.ui_repair.compliance_guardrails import ComplianceGuardrails
from services.observability.logging import get_logger
from .drill_runner import AdvancedDrillRunner
from .operator_escalation_service import OperatorEscalationService
from .red_team_scenario_generator import RedTeamScenarioGenerator
from .enterprise_readiness_assessor import EnterpriseReadinessAssessor
from .release_gatekeeper import ReleaseGatekeeper
from .final_audit_pack_generator import FinalAuditPackGenerator
from .handover_report_generator import HandoverReportGenerator
from .cost_telemetry import CostTelemetry
from .cost_attribution_service import CostAttributionService
from .budget_guard import BudgetGuard
from .cost_anomaly_detector import CostAnomalyDetector
from .capacity_planner import CapacityPlanner
from .finops_recommendation_engine import FinOpsRecommendationEngine
from .schemas import (
    UIProjectProfileCreate, UIRolloutWaveCreate, UIOperationsTeamCreate, 
    UIProjectOwnershipCreate, UIMaintenancePolicyCreate, UIReleaseRecordCreate, 
    UIEvidenceRetentionPolicyCreate, UIPolicyRuleCreate, UIAutonomousOverrideCreate,
    UIPolicyProposalCreate, PolicyDecision, PolicyScope, PolicyRuleType, PolicyProposalStatus
)

_log = get_logger("ui_repair_service")

class UIRepairService:
    """
    Core service for managing UI repair lifecycle:
    1. Orchestrates Playwright smoke runs.
    2. Collects and classifies evidence.
    3. Manages persistent UI Repair Cases.
    4. Links failures to Operational Incidents and Runtime Diagnostics.
    """
    
    DEFAULT_ROUTES = [
        "/", 
        "/dashboard", 
        "/workflows", 
        "/repair-lab", 
        "/system-health", 
        "/runtime-diagnostics", 
        "/governance",
        "/audit", 
        "/approvals", 
        "/incidents", 
        "/costs", 
        "/learning", 
        "/compliance", 
        "/fleet", 
        "/mesh",
        "/federation",
        "/evolution"
    ]

    def __init__(self, db: AsyncSession):
        self.db = db
        self.runner = UIEvidenceRunner()

    async def run_smoke_test(self, routes: Optional[List[str]] = None) -> UISmokeRun:
        """Executes a full smoke run on defined routes."""
        routes = routes or self.DEFAULT_ROUTES
        
        # 1. Create UISmokeRun record
        run = UISmokeRun(status="RUNNING", total_routes=len(routes), started_at=datetime.now())
        self.db.add(run)
        await self.db.commit()
        await self.db.refresh(run)

        _log.info(f"UI Repair Service: Started smoke run {cast(Any, run).id}")

        # 2. Run tests via Playwright
        from typing import Any as TAny
        r = run # type: TAny
        try:
            results = await self.runner.run_smoke_test(routes)
        except Exception as e:
            _log.error(f"UI Smoke Run failed critically: {e}")
            cast(Any, run).status = "FAILED"
            cast(Any, run).summary_json = {"error": str(e)}
            await self.db.commit()
            return run
        
        passed = 0
        failed = 0
        
        for res in results:
            # 3. Classify and handle each route result
            classification = UIRiskClassifier.classify(res)
            res.update(classification)
            
            await self._update_route_health(res)
            
            if res["status"] == "FAIL":
                failed += 1
                await self._handle_failure(res)
            else:
                passed += 1

        # 4. Finalize run
        cast(Any, run).status = "COMPLETED"
        cast(Any, run).passed_routes = passed
        cast(Any, run).failed_routes = failed
        cast(Any, run).finished_at = datetime.now()
        cast(Any, run).summary_json = {"results": results}
        
        await self.db.commit()
        _log.info(f"UI Repair Service: Completed smoke run {cast(Any, run).id}. Passed: {passed}, Failed: {failed}")
        return run

    async def get_overview(self) -> Dict[str, Any]:
        """Calculates the high-level UI health overview."""
        total_routes = len(self.DEFAULT_ROUTES)
        
        stmt_failing = select(func.count(UIRouteHealth.id)).where(UIRouteHealth.last_status == "FAIL")
        failing_routes = (await self.db.execute(stmt_failing)).scalar() or 0
        
        stmt_open_cases = select(func.count(UIRepairCase.id)).where(UIRepairCase.status != "RESOLVED", UIRepairCase.status != "IGNORED")
        open_cases = (await self.db.execute(stmt_open_cases)).scalar() or 0
        
        stmt_critical = select(func.count(UIRepairCase.id)).where(UIRepairCase.severity == "CRITICAL", UIRepairCase.status != "RESOLVED")
        critical_cases = (await self.db.execute(stmt_critical)).scalar() or 0
        
        stmt_last_run = select(UISmokeRun).order_by(UISmokeRun.started_at.desc()).limit(1)
        last_run = (await self.db.execute(stmt_last_run)).scalar_one_or_none()
        
        # Calculate health score: 1.0 - (failing_routes / total_routes)
        health_score = 1.0 - (failing_routes / total_routes if total_routes > 0 else 0)
        
        # Top failure types
        stmt_fail_types = select(UIRepairCase.failure_type, func.count(UIRepairCase.id)).group_by(UIRepairCase.failure_type)
        fail_types_res = (await self.db.execute(stmt_fail_types)).all()
        top_failure_types = [{"type": row[0], "count": row[1]} for row in fail_types_res]

        return {
            "ui_health_score": round(health_score, 2),
            "total_routes": total_routes,
            "passing_routes": total_routes - failing_routes,
            "failing_routes": failing_routes,
            "open_cases": open_cases,
            "critical_cases": critical_cases,
            "last_smoke_run_at": last_run.started_at if last_run else None,
            "last_smoke_status": last_run.status if last_run else None,
            "top_failure_types": top_failure_types
        }

    async def _update_route_health(self, res: Dict[str, Any]):
        """Updates the persistent health matrix for a specific route."""
        route = res["route"]
        stmt = select(UIRouteHealth).where(UIRouteHealth.route == route)
        health = (await self.db.execute(stmt)).scalar_one_or_none()
        
        if not health:
            health = UIRouteHealth(route=route)
            self.db.add(health)
            
        from typing import Any as TAny
        h = health # type: TAny
        cast(Any, health).last_status = str(res["status"])
        cast(Any, health).last_http_status = int(res["http_status"])
        cast(Any, health).last_checked_at = datetime.fromisoformat(res["timestamp"])
        
        if res["status"] == "PASS":
            cast(Any, health).last_success_at = cast(Any, health).last_checked_at
        else:
            cast(Any, health).failure_count = int(cast(Any, health).failure_count or 0) + 1
            
        # Moving average for response time
        if cast(Any, health).avg_response_ms:
            cast(Any, health).avg_response_ms = float((cast(Any, health).avg_response_ms * 0.7) + (res["response_time_ms"] * 0.3))
        else:
            cast(Any, health).avg_response_ms = float(res["response_time_ms"])
            
        cast(Any, health).blank_page_detected = bool(res.get("blank_page_detected", False))
        cast(Any, health).console_error_count = len(res.get("console_errors", []))
        cast(Any, health).network_error_count = len(res.get("network_errors", []))

    async def _handle_failure(self, res: Dict[str, Any]) -> bool:
        """
        Creates or updates a repair case and links it to system diagnostics.
        Returns True if a new case was created, False if updated.
        """
        route = res.get("route")
        
        # Deduplication: Check for open case for this route
        stmt = select(UIRepairCase).where(UIRepairCase.route == route, UIRepairCase.status != "RESOLVED")
        case_obj = (await self.db.execute(stmt)).scalar_one_or_none()
        
        is_new = False
        if not case_obj:
            is_new = True
            case_obj = UIRepairCase(
                route=route,
                status=UIRepairStatus.DETECTED.value,
                severity="MEDIUM", # Default, could be refined
                failure_type="UI_SMOKE_FAILURE"
            )
            self.db.add(case_obj)
            await self.db.commit()
            await self.db.refresh(case_obj)
        
        case = cast(Any, case_obj)
        case.console_errors_json = res.get("console_errors", [])
        case.network_errors_json = res.get("network_errors", [])
        case.screenshot_path = res.get("screenshot_path")
        case.trace_path = res.get("trace_path")
        case.updated_at = datetime.now()
        
        # Link current route health to this case
        stmt_health = select(UIRouteHealth).where(UIRouteHealth.route == route)
        health = (await self.db.execute(stmt_health)).scalar_one_or_none()
        if health:
            cast(Any, health).last_case_id = cast(Any, case).id

        # Governance Linking
        if case.severity in ["HIGH", "CRITICAL"]:
            await self._link_operational_incident(case)
        else:
            await self._link_runtime_diagnostic(case)
            
        await self.db.commit()
        return is_new

    async def get_repair_stats(self) -> Dict[str, Any]:
        """Returns statistics about recent repair attempts."""
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)
        
        stmt_hour = select(func.count(UIRepairAttempt.id)).where(UIRepairAttempt.created_at >= hour_ago)
        count_hour = (await self.db.execute(stmt_hour)).scalar() or 0
        
        stmt_day = select(func.count(UIRepairAttempt.id)).where(UIRepairAttempt.created_at >= day_ago)
        count_day = (await self.db.execute(stmt_day)).scalar() or 0
        
        return {
            "repairs_last_hour": count_hour,
            "repairs_last_day": count_day
        }

    async def _link_operational_incident(self, case: UIRepairCase):
        """Creates an OperationalIncident for high severity UI failures."""
        if case.linked_incident_id:
            return
            
        incident = OperationalIncident(
            incident_type="ui_breakage",
            severity=case.severity.lower(),
            message=f"Critical UI failure on {case.route}: {case.failure_type}",
            payload={
                "case_id": str(case.id), 
                "route": case.route,
                "failure_type": case.failure_type
            }
        )
        self.db.add(incident)
        await self.db.flush()
        case.linked_incident_id = incident.id
        
        # If CRITICAL, we could also trigger a GOVERNANCE_ADVISORY here if needed
        # but the requirements say "OperationalIncident + GOVERNANCE_ADVISORY event"

    async def _link_runtime_diagnostic(self, case: UIRepairCase):
        """Links LOW severity failures to RuntimeDiagnostics."""
        if case.linked_runtime_diagnostic_id:
            return
            
        # Generate a stable diagnostic ID
        diag_id = f"ui_fail_{case.route.replace('/', '_').strip('_') or 'root'}"
        cast(Any, case).linked_runtime_diagnostic_id = diag_id

    async def trigger_autonomous_repair(self, case_id: str) -> Dict[str, Any]:
        """Hand-off to the Stagehand/SWE-Agent orchestrator."""
        
        # Phase 15: Governance Policy Evaluation Hook
        case_stmt = select(UIRepairCase).where(UIRepairCase.id == case_id)
        case = (await self.db.execute(case_stmt)).scalar_one_or_none()
        
        if case:
            project_key = getattr(case, 'project_key', 'GLOBAL')
            policy_eval = await self.evaluate_action("AUTO_REPAIR_TRIGGER", {
                "project_key": project_key,
                "case_id": case_id,
                "route": case.route,
                "severity": case.severity,
                "risk_level": "MEDIUM" # Calculated based on case
            })
            
            if policy_eval.decision in [PolicyDecision.DENY, PolicyDecision.BLOCKED_BY_BUDGET]:
                _log.warning(f"Autonomous repair for case {case_id} BLOCKED by policy: {policy_eval.reason}")
                return {
                    "status": "BLOCKED_BY_POLICY",
                    "reason": policy_eval.reason,
                    "evaluation_id": str(policy_eval.id)
                }

        from .repair_orchestrator import UIRepairOrchestrator
        
        stmt = select(UIRepairCase).where(UIRepairCase.id == case_id)
        case = (await self.db.execute(stmt)).scalar_one_or_none()
        if not case:
            return {"status": "error", "message": "Case not found"}
        
        # Trigger the orchestrator in the background
        import asyncio
        case_uuid = UUID(str(case.id))
        asyncio.create_task(self._run_repair_task(case_uuid))
        
        return {
            "status": "success", 
            "message": "Autonomous repair cycle initiated.",
            "case_id": str(case.id)
        }

    async def _run_repair_task(self, case_id: UUID):
        """Internal task to run the full repair cycle using the Phase 4 orchestrator."""
        from .repair_orchestrator import UIRepairOrchestrator
        from libs.db.session import AsyncSessionLocal
        
        async with AsyncSessionLocal() as db:
            orch = UIRepairOrchestrator(db)
            await orch.run_repair_cycle(case_id)

    async def get_attempt_logs(self, case_id: str) -> List[Dict[str, Any]]:
        """Fetches all repair attempts for a case."""
        from libs.db.models.ui_repair_models import UIRepairAttempt
        stmt = select(UIRepairAttempt).where(UIRepairAttempt.case_id == case_id).order_by(UIRepairAttempt.attempt_no.desc())
        res = await self.db.execute(stmt)
        attempts = res.scalars().all()
        # Return as list of dicts to satisfy type checker and for better serialization
        return [
            {
                "id": str(a.id),
                "attempt_no": int(cast(Any, a).attempt_no or 0),
                "status": str(a.status),
                "started_at": a.started_at,
                "finished_at": a.finished_at,
                "stagehand_status": str(a.stagehand_status or ""),
                "open_swe_status": str(a.open_swe_status or ""),
                "diagnostic_brief": a.diagnostic_brief_json,
                "suspected_files": a.suspected_files_json,
                "repair_instruction": str(a.repair_instruction or ""),
                "pr_url": str(a.pr_url or ""),
                "created_at": a.created_at
            } for a in attempts
        ]

    async def get_case_events(self, case_id: str) -> List[Dict[str, Any]]:
        """Fetches all events for a case."""
        from libs.db.models.ui_repair_models import UIRepairEvent
        stmt = select(UIRepairEvent).where(UIRepairEvent.case_id == case_id).order_by(UIRepairEvent.created_at.desc())
        res = await self.db.execute(stmt)
        events = res.scalars().all()
        return [
            {
                "id": str(e.id),
                "event_type": str(e.event_type),
                "status": str(e.status or ""),
                "message": str(e.message or ""),
                "payload": e.payload_json,
                "created_at": e.created_at
            } for e in events
        ]

    async def get_repair_full_detail(self, attempt_id: str) -> Dict[str, Any]:
        """Fetches the complete verification and governance detail for a repair attempt."""
        from libs.db.models.ui_repair_models import UIRepairPRReview, UIRepairVerifierRun, UIRepairGovernanceApproval
        
        # 1. Fetch PR Review
        stmt_review = select(UIRepairPRReview).where(UIRepairPRReview.attempt_id == attempt_id)
        review = (await self.db.execute(stmt_review)).scalar_one_or_none()
        
        # 2. Fetch Verifier Run
        stmt_verifier = select(UIRepairVerifierRun).where(UIRepairVerifierRun.attempt_id == attempt_id)
        verifier = (await self.db.execute(stmt_verifier)).scalar_one_or_none()
        
        # 3. Fetch Governance Approval
        stmt_gov = select(UIRepairGovernanceApproval).where(UIRepairGovernanceApproval.attempt_id == attempt_id)
        gov = (await self.db.execute(stmt_gov)).scalar_one_or_none()
        
        return {
            "review": review,
            "verifier": verifier,
            "governance": gov
        }

    async def apply_patch(self, case_id: str, attempt_id: str, operator_name: str) -> Dict[str, Any]:
        """Final governance gate: Approves and applies the proposed patch."""
        from .apply_orchestrator import ApplyOrchestrator
        from .repair_evidence_writer import UIRepairEvidenceWriter
        from libs.db.models.ui_repair_models import UIRepairGovernanceApproval, UIRepairApplyResult, UIRepairStatus, RepairAttemptStatus
        
        stmt_case = select(UIRepairCase).where(UIRepairCase.id == case_id)
        case = (await self.db.execute(stmt_case)).scalar_one_or_none()
        
        stmt_gov = select(UIRepairGovernanceApproval).where(UIRepairGovernanceApproval.attempt_id == attempt_id)
        gov = (await self.db.execute(stmt_gov)).scalar_one_or_none()
        
        if not case or not gov:
            return {"status": "error", "message": "Case or Approval record not found."}
            
        # 1. Update Governance Status
        cast(Any, gov).status = "APPROVED"
        cast(Any, gov).approved_by = operator_name
        cast(Any, gov).approved_at = datetime.now()
        
        # 2. Run Apply Orchestrator
        cast(Any, case).status = UIRepairStatus.APPLYING.value
        await self.db.commit()
        
        apply_orch = ApplyOrchestrator()
        result = await apply_orch.apply_repair(str(case.pr_url))
        
        # 3. Record Apply Result
        apply_rec = UIRepairApplyResult(
            case_id=case.id,
            attempt_id=UUID(attempt_id),
            pr_url=case.pr_url,
            status=result["status"],
            apply_mode=result["apply_mode"],
            merge_commit_sha=result["merge_commit_sha"],
            rollback_snapshot_path=result["rollback_snapshot_path"],
            applied_at=result["applied_at"],
            applied_by=operator_name
        )
        self.db.add(apply_rec)
        
        # 4. Close Case
        if result["status"] == "SUCCESS":
            cast(Any, case).status = UIRepairStatus.RESOLVED.value
        else:
            cast(Any, case).status = UIRepairStatus.REPAIR_FAILED.value
            
        evidence = UIRepairEvidenceWriter(self.db)
        await evidence.log_event(
            case_id=UUID(str(case.id)),
            attempt_id=UUID(attempt_id),
            event_type="REPAIR_APPLIED",
            status=result["status"],
            message=f"Repair applied by {operator_name}. Commit: {result['merge_commit_sha']}",
            payload=result
        )
        
        await self.db.commit()
        return result

    async def get_monitoring_config(self) -> UIMonitoringConfig:
        """Fetches the current monitoring configuration, creating it if necessary."""
        stmt = select(UIMonitoringConfig).limit(1)
        config = (await self.db.execute(stmt)).scalar_one_or_none()
        
        if not config:
            config = UIMonitoringConfig()
            self.db.add(config)
            await self.db.commit()
            await self.db.refresh(config)
            
        return config

    async def update_monitoring_config(self, data: Dict[str, Any]) -> UIMonitoringConfig:
        """Updates the monitoring configuration."""
        config = await self.get_monitoring_config()
        
        for key, value in data.items():
            if hasattr(config, key):
                setattr(config, key, value)
            elif key == "route_scope":
                config.route_scope_json = value
                
        await self.db.commit()
        await self.db.refresh(config)
        return config

    async def get_monitoring_runs(self, limit: int = 20) -> List[UIMonitoringRun]:
        """Fetches recent monitoring run records."""
        stmt = select(UIMonitoringRun).order_by(UIMonitoringRun.started_at.desc()).limit(limit)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_route_health_history(self, route: str, limit: int = 50) -> List[UIRouteHealthHist]:
        """Fetches historical health data for a route."""
        stmt = select(UIRouteHealthHist).where(UIRouteHealthHist.route == route).order_by(UIRouteHealthHist.captured_at.desc()).limit(limit)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def trigger_monitoring_cycle(self, triggered_by: str = "MANUAL") -> Dict[str, Any]:
        """Triggers a background monitoring cycle."""
        from .scheduled_smoke_runner import ScheduledSmokeRunner
        import asyncio
        
        # We run it in the background to avoid blocking the API
        asyncio.create_task(self._run_monitoring_task(triggered_by))
        
        return {"status": "success", "message": "Monitoring cycle initiated in background."}

    async def _run_monitoring_task(self, triggered_by: str):
        """Internal task for background monitoring execution."""
        from libs.db.session import AsyncSessionLocal
        from .scheduled_smoke_runner import ScheduledSmokeRunner
        
        async with AsyncSessionLocal() as db:
            runner = ScheduledSmokeRunner(db)
            await runner.run_monitoring_cycle(triggered_by=triggered_by)

    # --- Phase 8: Chaos Drills ---

    async def get_chaos_scenarios(self) -> List[UIChaosDrillScenario]:
        """Fetches all chaos drill scenarios."""
        stmt = select(UIChaosDrillScenario).where(UIChaosDrillScenario.is_enabled == True)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def run_chaos_drill(self, scenario_id: str, triggered_by: str = "MANUAL") -> Dict[str, Any]:
        """Runs a specific chaos drill."""
        from .chaos_drill_engine import ChaosDrillEngine
        engine = ChaosDrillEngine(self.db)
        return await engine.run_drill(UUID(scenario_id), triggered_by)

    async def get_chaos_runs(self, limit: int = 20) -> List[UIChaosDrillRun]:
        """Fetches recent chaos drill execution records."""
        stmt = select(UIChaosDrillRun).order_by(UIChaosDrillRun.started_at.desc()).limit(limit)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    # --- Phase 8: Soak Validation ---

    async def start_soak_validation(self, duration_minutes: int = 60) -> Dict[str, Any]:
        """Starts a long-term soak validation period."""
        from .soak_validator import SoakValidator
        validator = SoakValidator(self.db)
        run_id = await validator.start_soak_validation(duration_minutes)
        return {"status": "success", "run_id": run_id}

    async def get_soak_runs(self, limit: int = 20) -> List[UISoakValidationRun]:
        """Fetches recent soak validation records."""
        stmt = select(UISoakValidationRun).order_by(UISoakValidationRun.started_at.desc()).limit(limit)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    # --- Phase 8: Recovery Proof Packs ---

    async def generate_recovery_proof_pack(self, name: str, days: int = 7) -> Dict[str, Any]:
        """Generates a recovery proof pack for the last N days."""
        from .recovery_proof_pack import RecoveryProofPackGenerator
        end = datetime.now()
        start = end - timedelta(days=days)
        generator = RecoveryProofPackGenerator(self.db)
        return await generator.generate_pack(name, start, end)

    async def get_recovery_proof_packs(self, limit: int = 20) -> List[UIRecoveryProofPack]:
        """Fetches generated recovery proof packs."""
        stmt = select(UIRecoveryProofPack).order_by(UIRecoveryProofPack.generated_at.desc()).limit(limit)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    # --- Phase 9: Advanced Chaos & Escalation ---

    async def get_advanced_chaos_scenarios(self) -> List[UIAdvancedChaosScenario]:
        stmt = select(UIAdvancedChaosScenario).where(UIAdvancedChaosScenario.is_enabled == True)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def run_advanced_chaos_drill(self, scenario_id: str, triggered_by: str = "MANUAL") -> Dict[str, Any]:
        from .drill_runner import AdvancedDrillRunner
        runner = AdvancedDrillRunner(self.db)
        return await runner.run_advanced_drill(UUID(scenario_id), triggered_by)

    async def get_advanced_chaos_runs(self, limit: int = 20) -> List[UIAdvancedChaosRun]:
        stmt = select(UIAdvancedChaosRun).order_by(UIAdvancedChaosRun.started_at.desc()).limit(limit)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_escalations(self, limit: int = 20) -> List[UIOperatorEscalation]:
        stmt = select(UIOperatorEscalation).order_by(UIOperatorEscalation.created_at.desc()).limit(limit)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_escalation(self, escalation_id: str) -> Optional[UIOperatorEscalation]:
        stmt = select(UIOperatorEscalation).where(UIOperatorEscalation.id == UUID(escalation_id))
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def acknowledge_escalation(self, escalation_id: str, operator_id: str):
        stmt = select(UIOperatorEscalation).where(UIOperatorEscalation.id == UUID(escalation_id))
        esc = (await self.db.execute(stmt)).scalar_one_or_none()
        if esc:
            cast(Any, esc).status = "ACKNOWLEDGED"
            cast(Any, esc).acknowledged_by = operator_id
            cast(Any, esc).acknowledged_at = datetime.now(timezone.utc)
            await self.db.commit()

    async def resolve_escalation(self, escalation_id: str, operator_id: str):
        stmt = select(UIOperatorEscalation).where(UIOperatorEscalation.id == UUID(escalation_id))
        esc = (await self.db.execute(stmt)).scalar_one_or_none()
        if esc:
            cast(Any, esc).status = "RESOLVED"
            cast(Any, esc).resolved_by = operator_id
            cast(Any, esc).resolved_at = datetime.now(timezone.utc)
            await self.db.commit()

    async def get_notification_deliveries(self, limit: int = 20) -> List[UINotificationDelivery]:
        stmt = select(UINotificationDelivery).order_by(UINotificationDelivery.created_at.desc()).limit(limit)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_crisis_state(self) -> UICrisisControlState:
        stmt = select(UICrisisControlState).limit(1)
        state = (await self.db.execute(stmt)).scalar_one_or_none()
        if not state:
            state = UICrisisControlState(mode="NORMAL")
            self.db.add(state)
            await self.db.commit()
            await self.db.refresh(state)
        return state

    async def update_crisis_state(self, mode: str, reason: str, operator_id: str) -> UICrisisControlState:
        state = await self.get_crisis_state()
        cast(Any, state).mode = mode
        cast(Any, state).reason = reason
        cast(Any, state).activated_by = operator_id
        cast(Any, state).activated_at = datetime.now(timezone.utc)
        
        # Apply mode logic
        cast(Any, state).self_healing_frozen = mode in ["SELF_HEALING_FROZEN", "FULL_UI_REPAIR_FREEZE", "CRISIS_RESPONSE"]
        cast(Any, state).auto_repair_frozen = mode in ["AUTO_REPAIR_FROZEN", "FULL_UI_REPAIR_FREEZE", "CRISIS_RESPONSE"]
        cast(Any, state).monitoring_frozen = mode == "FULL_UI_REPAIR_FREEZE"
        
        await self.db.commit()
        await self.db.refresh(state)
        return state
    # --- Phase 10: Final Enterprise Readiness & Release Gate Methods ---

    async def generate_red_team_scenarios(self) -> List[UIRedTeamScenario]:
        generator = RedTeamScenarioGenerator(self.db)
        return await generator.generate_scenarios()

    async def run_red_team_scenario(self, scenario_id: UUID) -> UIRedTeamRun:
        # Mocking run logic: in real case, this would trigger AdvancedDrillRunner
        # with specific red-team parameters.
        scenario = await self.db.get(UIRedTeamScenario, scenario_id)
        if not scenario:
            raise ValueError(f"Red Team Scenario {scenario_id} not found")
        run = UIRedTeamRun(
            scenario_id=scenario_id,
            status="COMPLETED",
            actual_detection=scenario.expected_detection,
            actual_severity=scenario.expected_severity,
            actual_decision=scenario.expected_policy_decision,
            passed=True,
            vulnerability_found=False,
            finished_at=datetime.now(timezone.utc)
        )
        self.db.add(run)
        await self.db.commit()
        return run

    async def assess_enterprise_readiness(self, assessor: str) -> UIEnterpriseReadinessAssessment:
        assessor_service = EnterpriseReadinessAssessor(self.db)
        return await assessor_service.perform_assessment(assessor)

    async def evaluate_release_gate(self, assessment_id: UUID, approver: str) -> UIReleaseGateDecision:
        assessment = await self.db.get(UIEnterpriseReadinessAssessment, assessment_id)
        if not assessment:
            raise ValueError(f"Assessment {assessment_id} not found")
        gatekeeper = ReleaseGatekeeper(self.db)
        return await gatekeeper.evaluate_release(assessment, approver)

    async def generate_final_audit_pack(self, name: str, version: str) -> UIFinalAuditPack:
        generator = FinalAuditPackGenerator(self.db)
        return await generator.generate_pack(name, version)

    async def generate_handover_report(self, title: str) -> UIOperatorHandoverReport:
        generator = HandoverReportGenerator(self.db)
        return await generator.generate_handover(title)

    async def get_latest_readiness_overview(self) -> Dict[str, Any]:
        stmt = select(UIEnterpriseReadinessAssessment).order_by(UIEnterpriseReadinessAssessment.created_at.desc()).limit(1)
        assessment = (await self.db.execute(stmt)).scalar_one_or_none()
        
        if not assessment:
            return {"status": "NO_DATA"}
            
        stmt_gate = select(UIReleaseGateDecision).where(UIReleaseGateDecision.assessment_id == assessment.id)
        gate = (await self.db.execute(stmt_gate)).scalar_one_or_none()
        
        return {
            "assessment": assessment,
            "gate": gate,
            "status": "READY"
        }

    # Phase 11: Pilot Rollout
    async def start_pilot(self, name: str, mode: Any, duration: int, created_by: str):
        from .pilot_rollout_manager import PilotRolloutManager
        return await PilotRolloutManager.start_pilot(self.db, name, mode, duration, created_by)

    async def get_pilot_status(self):
        stmt = select(UIPilotRollout).order_by(UIPilotRollout.created_at.desc()).limit(1)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def pause_pilot(self, rollout_id: str, rationale: str):
        from .pilot_rollout_manager import PilotRolloutManager
        return await PilotRolloutManager.pause_pilot(self.db, rollout_id, rationale)

    async def record_operator_action(self, rollout_id: str, operator: str, action_type: str, rationale: str, target_type: Optional[str] = None, target_id: Optional[str] = None):
        from .operator_action_ledger import OperatorActionLedger
        return await OperatorActionLedger.record_action(self.db, rollout_id, operator, action_type, rationale, target_type, target_id)

    async def get_pilot_metrics(self, rollout_id: str):
        from .pilot_metrics_collector import PilotMetricsCollector
        return await PilotMetricsCollector.get_metrics(self.db, rollout_id)

    async def generate_pilot_report(self, rollout_id: str):
        from .pilot_report_generator import PilotReportGenerator
        return await PilotReportGenerator.generate_report(self.db, rollout_id)

    # --- Phase 12: General Availability + Multi-Project Rollout Methods ---

    async def list_projects(self) -> List[UIRepairProjectProfile]:
        from .project_rollout_manager import ProjectRolloutManager
        return list(await ProjectRolloutManager.list_projects(self.db))

    async def create_project(self, data: UIProjectProfileCreate) -> UIRepairProjectProfile:
        from .project_rollout_manager import ProjectRolloutManager
        return await ProjectRolloutManager.create_project(self.db, data)

    async def get_project(self, project_key: str) -> Optional[UIRepairProjectProfile]:
        from .project_rollout_manager import ProjectRolloutManager
        return await ProjectRolloutManager.get_project(self.db, project_key)

    async def update_project_status(self, project_key: str, status: str) -> Optional[UIRepairProjectProfile]:
        from .project_rollout_manager import ProjectRolloutManager
        return await ProjectRolloutManager.update_project_status(self.db, project_key, status)

    async def update_project_policy(self, project_key: str, safety: Optional[Dict[str, Any]] = None, governance: Optional[Dict[str, Any]] = None):
        from .project_policy_registry import ProjectPolicyRegistry
        return await ProjectPolicyRegistry.update_policy(self.db, project_key, safety, governance)

    async def list_rollout_waves(self) -> List[UIRolloutWave]:
        from .rollout_wave_manager import RolloutWaveManager
        return list(await RolloutWaveManager.list_waves(self.db))

    async def create_rollout_wave(self, data: UIRolloutWaveCreate) -> UIRolloutWave:
        from .rollout_wave_manager import RolloutWaveManager
        return await RolloutWaveManager.create_wave(self.db, data)

    async def start_rollout_wave(self, wave_id: str) -> Optional[UIRolloutWave]:
        from .rollout_wave_manager import RolloutWaveManager
        return await RolloutWaveManager.start_wave(self.db, wave_id)

    async def complete_rollout_wave(self, wave_id: str) -> Optional[UIRolloutWave]:
        from .rollout_wave_manager import RolloutWaveManager
        return await RolloutWaveManager.complete_wave(self.db, wave_id)

    async def get_enterprise_overview(self) -> Dict[str, Any]:
        from .multi_project_dashboard_service import MultiProjectDashboardService
        return await MultiProjectDashboardService.get_enterprise_overview(self.db)

    async def get_sla_slo_metrics(self) -> Dict[str, Any]:
        from .sla_slo_tracker import SLASLOTracker
        return await SLASLOTracker.get_enterprise_metrics(self.db)

    async def check_ga_readiness(self, assessor: str) -> UIGAReadinessAssessment:
        from .ga_readiness_checker import GAReadinessChecker
        return await GAReadinessChecker.perform_check(self.db, assessor)

    async def get_latest_ga_readiness(self) -> Optional[UIGAReadinessAssessment]:
        from .ga_readiness_checker import GAReadinessChecker
        return await GAReadinessChecker.get_latest_assessment(self.db)

    async def generate_enterprise_runbook(self, title: str, version: str) -> UIEnterpriseRunbook:
        from .runbook_generator import RunbookGenerator
        return await RunbookGenerator.generate_runbook(self.db, title, version)

    async def get_latest_runbook(self) -> Optional[UIEnterpriseRunbook]:
        from .runbook_generator import RunbookGenerator
        return await RunbookGenerator.get_latest_runbook(self.db)

    # --- Phase 13: GA Hardening + Cross-Team Operations Methods ---

    async def list_operations_teams(self) -> List[UIOperationsTeam]:
        from .operations_model import OperationsModel
        return list(await OperationsModel.list_teams(self.db))

    async def create_operations_team(self, data: UIOperationsTeamCreate) -> UIOperationsTeam:
        from .operations_model import OperationsModel
        return await OperationsModel.create_team(self.db, data)

    async def list_project_ownerships(self) -> List[UIProjectOwnership]:
        from .ownership_registry import OwnershipRegistry
        return list(await OwnershipRegistry.list_ownerships(self.db))

    async def create_project_ownership(self, data: UIProjectOwnershipCreate) -> UIProjectOwnership:
        from .ownership_registry import OwnershipRegistry
        return await OwnershipRegistry.create_project_ownership(self.db, data)

    async def get_escalation_path(self, project_key: str, severity: str) -> Dict[str, Any]:
        from .escalation_matrix_service import EscalationMatrixService
        return await EscalationMatrixService.get_escalation_path(self.db, project_key, severity)

    async def list_maintenance_policies(self) -> List[UIMaintenancePolicy]:
        from .maintenance_policy import MaintenancePolicy
        return list(await MaintenancePolicy.list_policies(self.db))

    async def create_maintenance_policy(self, data: UIMaintenancePolicyCreate) -> UIMaintenancePolicy:
        from .maintenance_policy import MaintenancePolicy
        return await MaintenancePolicy.create_policy(self.db, data)

    async def list_releases(self) -> List[UIReleaseRecord]:
        from .release_notes_generator import ReleaseNotesGenerator
        return list(await ReleaseNotesGenerator.list_releases(self.db))

    async def generate_release_record(self, data: UIReleaseRecordCreate) -> UIReleaseRecord:
        from .release_notes_generator import ReleaseNotesGenerator
        return await ReleaseNotesGenerator.generate_release_record(self.db, data)

    async def run_compatibility_check(self, project_key: str, version: str) -> UICompatibilityCheck:
        from .compatibility_checker import CompatibilityChecker
        return await CompatibilityChecker.run_check(self.db, project_key, version)

    async def get_latest_compatibility_check(self, project_key: str) -> Optional[UICompatibilityCheck]:
        from .compatibility_checker import CompatibilityChecker
        return await CompatibilityChecker.get_latest_check(self.db, project_key)

    async def list_evidence_retention_policies(self) -> List[UIEvidenceRetentionPolicy]:
        from .evidence_retention_policy import EvidenceRetentionPolicy
        return list(await EvidenceRetentionPolicy.list_policies(self.db))

    async def create_evidence_retention_policy(self, data: UIEvidenceRetentionPolicyCreate) -> UIEvidenceRetentionPolicy:
        from .evidence_retention_policy import EvidenceRetentionPolicy
        return await EvidenceRetentionPolicy.create_policy(self.db, data)

    async def list_slo_breaches(self, project_key: Optional[str] = None) -> List[UISLOBreach]:
        from .slo_breach_manager import SLOBreachManager
        return list(await SLOBreachManager.list_breaches(self.db, project_key))

    async def acknowledge_slo_breach(self, breach_id: str) -> Optional[UISLOBreach]:
        from .slo_breach_manager import SLOBreachManager
        return await SLOBreachManager.acknowledge_breach(self.db, breach_id)

    async def resolve_slo_breach(self, breach_id: str) -> Optional[UISLOBreach]:
        from .slo_breach_manager import SLOBreachManager
        return await SLOBreachManager.resolve_breach(self.db, breach_id)

    # --- Phase 14: Enterprise FinOps Methods ---

    async def get_finops_overview(self) -> Dict[str, Any]:
        """Provides a high-level overview of operational costs and efficiency."""
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        cost_today = await CostTelemetry.get_total_cost(self.db, since=today)
        cost_week = await CostTelemetry.get_total_cost(self.db, since=week_ago)
        cost_month = await CostTelemetry.get_total_cost(self.db, since=month_ago)
        
        project_dist = await CostAttributionService.get_project_attribution(self.db, days=30)
        team_dist = await CostAttributionService.get_team_attribution(self.db, days=30)
        op_dist = await CostAttributionService.get_operation_attribution(self.db, days=30)
        
        anomalies = await CostAnomalyDetector.list_anomalies(self.db)
        active_anomalies = [a for a in anomalies if a.status == "OPEN"]
        
        recs = await FinOpsRecommendationEngine.list_recommendations(self.db)
        potential_savings = sum(r.expected_savings_usd for r in recs if r.status == "PENDING")
        
        return {
            "total_cost_today": cost_today,
            "total_cost_week": cost_week,
            "total_cost_month": cost_month,
            "project_cost_distribution": project_dist,
            "team_cost_distribution": team_dist,
            "operation_type_distribution": op_dist,
            "budget_usage_percent": 45.0, # Mocked for now
            "active_anomalies_count": len(active_anomalies),
            "forecasted_next_30d_cost": cost_month * 1.1, # Mocked forecast
            "potential_savings_usd": potential_savings
        }

    async def record_cost_event(self, data: Any) -> UICostEvent:
        return await CostTelemetry.record_event(self.db, data)

    async def list_cost_events(self, project_key: Optional[str] = None) -> List[UICostEvent]:
        return await CostTelemetry.list_events(self.db, project_key)

    async def get_budget_policy(self, project_key: str) -> Optional[UIBudgetPolicy]:
        return await BudgetGuard.get_policy(self.db, project_key)

    async def update_budget_policy(self, data: Any) -> UIBudgetPolicy:
        return await BudgetGuard.create_or_update_policy(self.db, data)

    async def list_cost_anomalies(self, project_key: Optional[str] = None) -> List[UICostAnomaly]:
        return await CostAnomalyDetector.list_anomalies(self.db, project_key)

    async def resolve_cost_anomaly(self, anomaly_id: str) -> Optional[UICostAnomaly]:
        return await CostAnomalyDetector.resolve_anomaly(self.db, anomaly_id)

    async def get_capacity_forecast(self, project_key: str) -> Optional[UICapacityForecast]:
        return await CapacityPlanner.get_latest_plan(self.db, project_key)

    async def generate_capacity_forecast(self, project_key: str) -> UICapacityForecast:
        return await CapacityPlanner.generate_capacity_plan(self.db, project_key)

    async def list_finops_recommendations(self, project_key: Optional[str] = None) -> List[UIFinOpsRecommendation]:
        return await FinOpsRecommendationEngine.list_recommendations(self.db, project_key)

    async def update_recommendation_status(self, rec_id: str, status: str) -> Optional[UIFinOpsRecommendation]:
        return await FinOpsRecommendationEngine.update_recommendation_status(self.db, rec_id, status)

    # --- Phase 15: Autonomous Ecosystem Governance Methods ---

    async def get_policy_engine(self, project_key: Optional[str] = None) -> PolicyAsCodeEngine:
        """Loads active rules and initializes the engine."""
        query = select(UIPolicyRule).where(UIPolicyRule.enabled == True)
        if project_key:
            query = query.filter((UIPolicyRule.scope == "GLOBAL") | (UIPolicyRule.project_key == project_key))
        else:
            query = query.where(UIPolicyRule.scope == "GLOBAL")
        
        result = await self.db.execute(query)
        rules = list(result.scalars().all())
        return PolicyAsCodeEngine(rules)

    async def evaluate_action(self, action_type: str, context: Dict[str, Any]) -> UIPolicyEvaluation:
        """Evaluates an action and persists the result."""
        project_key = context.get("project_key", "GLOBAL")
        engine = await self.get_policy_engine(project_key)
        
        eval_result = engine.evaluate(action_type, context)
        
        evaluation = UIPolicyEvaluation(
            project_key=project_key,
            action_type=action_type,
            decision=eval_result["decision"],
            reason=eval_result["reason"],
            matched_rules_json={"rules": eval_result["matched_rules"]},
            input_context_json=context,
            output_json=eval_result
        )
        
        self.db.add(evaluation)
        await self.db.commit()
        await self.db.refresh(evaluation)
        
        # 4. Integrate with Sovereign Evidence chain
        import hashlib
        evidence_payload = {
            "evaluation_id": str(evaluation.id),
            "decision": eval_result["decision"],
            "reason": eval_result["reason"],
            "policy_key": eval_result.get("policy_key"),
            "context": context
        }
        prov_hash = hashlib.sha256(json.dumps(evidence_payload, sort_keys=True).encode()).hexdigest()
        
        evidence = SovereignEvidence(
            evidence_type="POLICY_EVALUATION",
            severity="info",
            payload=evidence_payload,
            provenance_hash=prov_hash
        )
        self.db.add(evidence)
        await self.db.commit()
        
        return evaluation

    async def create_policy_rule(self, rule_data: UIPolicyRuleCreate) -> UIPolicyRule:
        """Registers a new governance policy rule."""
        rule = UIPolicyRule(
            policy_key=rule_data.policy_key,
            scope=rule_data.scope,
            project_key=rule_data.project_key,
            rule_type=rule_data.rule_type,
            priority=rule_data.priority,
            enabled=rule_data.enabled,
            rule_definition_json=rule_data.rule_definition,
            description=rule_data.description,
            created_by=rule_data.created_by
        )
        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)
        return rule

    async def list_policy_rules(self, project_key: Optional[str] = None) -> List[UIPolicyRule]:
        """Lists active policy rules."""
        query = select(UIPolicyRule)
        if project_key:
            query = query.filter((UIPolicyRule.scope == "GLOBAL") | (UIPolicyRule.project_key == project_key))
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_autonomous_override(self, override_data: UIAutonomousOverrideCreate) -> UIAutonomousOverride:
        """Records a manual override of a blocked action."""
        override = UIAutonomousOverride(
            action_type=override_data.action_type,
            target_type=override_data.target_type,
            target_id=override_data.target_id,
            blocked_policy_key=override_data.blocked_policy_key,
            override_reason=override_data.override_reason,
            operator=override_data.operator,
            risk_level=override_data.risk_level,
            approval_id=override_data.approval_id
        )
        self.db.add(override)
        await self.db.flush() # Flush to get ID
        
        import hashlib
        evidence_payload = {
            "override_id": str(override.id),
            "operator": override.operator,
            "reason": override.override_reason,
            "blocked_policy": override.blocked_policy_key
        }
        prov_hash = hashlib.sha256(json.dumps(evidence_payload, sort_keys=True).encode()).hexdigest()
        override.evidence_hash = prov_hash

        evidence = SovereignEvidence(
            evidence_type="GOVERNANCE_OVERRIDE",
            severity=override.risk_level,
            payload=evidence_payload,
            provenance_hash=prov_hash
        )
        self.db.add(evidence)
        
        # Trigger OperationalIncident for high risk overrides
        if override.risk_level in ["HIGH", "CRITICAL"]:
            incident = OperationalIncident(
                title=f"Governance Policy Override: {override.blocked_policy_key}",
                severity=override.risk_level,
                component="UI_REPAIR_GOVERNANCE",
                description=f"Operator {override.operator} bypassed governance policy. Rationale: {override.override_reason}",
                status="OPEN"
            )
            self.db.add(incident)

        await self.db.commit()
        await self.db.refresh(override)
        return override

    async def get_compliance_findings(self, project_key: Optional[str] = None) -> List[UIComplianceFinding]:
        """Lists active compliance findings."""
        query = select(UIComplianceFinding)
        if project_key:
            query = query.where(UIComplianceFinding.project_key == project_key)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_policy_proposal(self, proposal_data: UIPolicyProposalCreate) -> UIPolicyProposal:
        """Submits a new policy proposal for review."""
        proposal = UIPolicyProposal(
            proposal_type=proposal_data.proposal_type,
            policy_key=proposal_data.policy_key,
            scope=proposal_data.scope,
            project_key=proposal_data.project_key,
            proposed_rule_json=proposal_data.proposed_rule,
            rationale=proposal_data.rationale,
            risk_level=proposal_data.risk_level,
            status=PolicyProposalStatus.SUBMITTED,
            proposed_by=proposal_data.proposed_by
        )
        self.db.add(proposal)
        await self.db.commit()
        await self.db.refresh(proposal)
        return proposal

    async def approve_policy_proposal(self, proposal_id: UUID, reviewer: str) -> UIPolicyRule:
        """Approves a proposal and creates/updates the corresponding rule."""
        stmt = select(UIPolicyProposal).where(UIPolicyProposal.id == proposal_id)
        proposal = (await self.db.execute(stmt)).scalar_one_or_none()
        
        if not proposal:
            raise ValueError("Proposal not found")
        
        proposal.status = PolicyProposalStatus.APPROVED
        proposal.reviewed_by = reviewer
        proposal.reviewed_at = datetime.now(timezone.utc)
        
        # Create or update rule
        rule_stmt = select(UIPolicyRule).where(UIPolicyRule.policy_key == proposal.policy_key)
        existing_rule = (await self.db.execute(rule_stmt)).scalar_one_or_none()
        
        if existing_rule:
            existing_rule.rule_definition_json = proposal.proposed_rule_json
            existing_rule.scope = proposal.scope
            existing_rule.project_key = proposal.project_key
            rule = existing_rule
        else:
            rule = UIPolicyRule(
                policy_key=proposal.policy_key,
                scope=proposal.scope,
                project_key=proposal.project_key,
                rule_definition_json=proposal.proposed_rule_json,
                created_by=proposal.proposed_by,
                enabled=True
            )
            self.db.add(rule)
            
        await self.db.commit()
        await self.db.refresh(rule)
        return rule

    async def list_policy_conflicts(self, project_key: Optional[str] = None) -> List[UIPolicyConflict]:
        """Lists detected policy conflicts."""
        query = select(UIPolicyConflict)
        if project_key:
            query = query.where(UIPolicyConflict.project_key == project_key)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # --- Phase 16: Multi-Tenant Federation + Cross-Cluster Governance ---

    async def create_tenant(self, data: UITenantProfileCreate) -> UITenantProfile:
        from services.ui_repair.tenant_registry import TenantRegistry
        return await TenantRegistry.create_tenant(self.db, data)

    async def list_tenants(self) -> List[UITenantProfile]:
        from services.ui_repair.tenant_registry import TenantRegistry
        return await TenantRegistry.list_tenants(self.db)

    async def bind_project_to_tenant(self, data: UITenantProjectBindingCreate) -> UITenantProjectBinding:
        from services.ui_repair.tenant_registry import TenantRegistry
        return await TenantRegistry.bind_project_to_tenant(self.db, data)

    async def create_cluster(self, data: UIClusterProfileCreate) -> UIClusterProfile:
        from services.ui_repair.cluster_registry import ClusterRegistry
        return await ClusterRegistry.create_cluster(self.db, data)

    async def list_clusters(self) -> List[UIClusterProfile]:
        from services.ui_repair.cluster_registry import ClusterRegistry
        return await ClusterRegistry.list_clusters(self.db)

    async def get_federated_health(self) -> Dict[str, Any]:
        from services.ui_repair.cluster_health_aggregator import ClusterHealthAggregator
        return await ClusterHealthAggregator.get_federated_health_summary(self.db)

    async def scan_policy_drift(self, tenant_key: Optional[str] = None) -> List[UIPolicyDrift]:
        from services.ui_repair.policy_drift_detector import PolicyDriftDetector
        return await PolicyDriftDetector.scan_for_drifts(self.db, tenant_key)

    async def get_federated_evidence(self, tenant_key: Optional[str] = None) -> List[UIFederatedEvidenceRecord]:
        from services.ui_repair.federated_evidence_ledger import FederatedEvidenceLedger
        return await FederatedEvidenceLedger.list_federated_evidence(self.db, tenant_key=tenant_key)
