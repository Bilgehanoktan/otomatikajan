import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, cast
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, desc

from libs.db.models.ui_repair_models import (
    UIRepairCase, UIRouteHealth, UISmokeRun, UIRepairStatus, FailureType, UIRepairSeverity,
    UIMonitoringConfig, UIMonitoringRun, UIRouteHealthHist, UIRepairAttempt,
    UIChaosDrillScenario, UIChaosDrillRun, UISoakValidationRun, UIRecoveryProofPack,
    UIAdvancedChaosScenario, UIAdvancedChaosRun, UIOperatorEscalation, UINotificationDelivery, UICrisisControlState,
    UIRedTeamScenario, UIRedTeamRun, UIEnterpriseReadinessAssessment, UIReleaseGateDecision, UIFinalAuditPack, UIOperatorHandoverReport
)
from libs.db.models.core_models import OperationalIncident, SovereignEvidence
from services.ui_repair.playwright_runner import UIEvidenceRunner
from services.ui_repair.risk_classifier import UIRiskClassifier
from services.observability.logging import get_logger
from .drill_runner import AdvancedDrillRunner
from .operator_escalation_service import OperatorEscalationService
from .red_team_scenario_generator import RedTeamScenarioGenerator
from .enterprise_readiness_assessor import EnterpriseReadinessAssessor
from .release_gatekeeper import ReleaseGatekeeper
from .final_audit_pack_generator import FinalAuditPackGenerator
from .handover_report_generator import HandoverReportGenerator

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
            cast(Any, esc).acknowledged_at = datetime.utcnow()
            await self.db.commit()

    async def resolve_escalation(self, escalation_id: str, operator_id: str):
        stmt = select(UIOperatorEscalation).where(UIOperatorEscalation.id == UUID(escalation_id))
        esc = (await self.db.execute(stmt)).scalar_one_or_none()
        if esc:
            cast(Any, esc).status = "RESOLVED"
            cast(Any, esc).resolved_by = operator_id
            cast(Any, esc).resolved_at = datetime.utcnow()
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
        cast(Any, state).activated_at = datetime.utcnow()
        
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
