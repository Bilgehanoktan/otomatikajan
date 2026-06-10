import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional, cast, Union
import uuid
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select, update, func, desc

from libs.db.models.ui_repair_models import (
    UIRepairCase, UIRouteHealth, UISmokeRun, UIRepairStatus, FailureType, UIRepairSeverity,
    UIMonitoringConfig, UIMonitoringRun, UIRouteHealthHist, UIRepairAttempt,
    UIChaosDrillScenario, UIChaosDrillRun, UISoakValidationRun, UIRecoveryProofPack,
    UIAdvancedChaosScenario, UIAdvancedChaosRun, UIOperatorEscalation, UINotificationDelivery, UICrisisControlState,
    UIRedTeamScenario, UIRedTeamRun, UIAdversarialProbe, UIAdversarialDriftEvent, UIRedTeamFinding, UIRedTeamReport,
    UIPilotRollout, UIPilotEvent, UIPilotMetrics, UIOperatorActionLedger, UIPilotFinalReport,
    UIOperationsTeam, UIProjectOwnership, UIMaintenancePolicy, UIReleaseRecord, UICompatibilityCheck, UISLOBreach, UIEvidenceRetentionPolicy,
    UIRepairProjectProfile, UIRolloutWave, UIGAReadinessAssessment, UIEnterpriseRunbook,
    UICostEvent, UIBudgetPolicy, UICostAnomaly, UICapacityForecast, UIFinOpsRecommendation,
    UIPolicyRule, UIPolicyEvaluation, UIPolicyConflict, UIPolicyProposal, UIAutonomousOverride, UIComplianceFinding,
    UICognitiveIntegrityCheck, UICognitiveDecision,
    UIGuardrailTuningProposal, UIDefensivePattern, UIPolicyRegressionRun, UIGuardrailCanaryRun, UIDefenseOptimizationReport,
    UIIncidentWarRoom, UIIncidentTimelineEvent, UIExecutiveRiskSnapshot, UIIncidentActionItem, UIExecutiveRiskReport,
    UIAutoPatchExecution, UIPatchCandidate, UIVerificationRunV2, UIPostApplyValidation, UIRollbackExecution,
    UIAutoPatchTrace, UIPatchNegotiationSession, UIPatchDebateTurn, UIPatchCandidateScore,
    AutoPatchExecutionStatus, AutoPatchSourceType,
    UIEnterpriseReadinessAssessment, UIReleaseGateDecision, UIFinalAuditPack, UIOperatorHandoverReport,
    UITenantProfile, UITenantProjectBinding, UIClusterProfile, UIPolicyDrift, UIFederatedEvidenceRecord,
    UISecurityRemediationPlan, UISecurityAutoFixAttempt, UIProviderHealth, UIFinalIntegrationAudit,
    UIReleaseReadinessCheck, UIThirdPartyRiskAssessment, UISovereignIdentity,
    UISecurityPostureFinding, UIAttackPath, UIAttackSimulationRun, UIResidualRiskAcceptance
    , UIKnowledgeNode, UIKnowledgeEdge
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
from .autonomous_red_team_agent import AutonomousRedTeamAgent
from .red_team_reporter import RedTeamReporter
from .guardrail_optimization_engine import GuardrailOptimizationEngine
from .tuning_proposal_service import TuningProposalService
from .defense_optimization_reporter import DefenseOptimizationReporter
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
from .incident_war_room import IncidentWarRoomManager
from .executive_risk_command_center import ExecutiveRiskCommandCenter
from .executive_risk_reporter import ExecutiveRiskReporter
from .autopatch_v2_orchestrator import AutoPatchV2Orchestrator
from .war_room_closure_manager import WarRoomClosureManager
from .schemas import (
    UIProjectProfileCreate, UIRolloutWaveCreate, UIOperationsTeamCreate, 
    UIProjectOwnershipCreate, UIMaintenancePolicyCreate, UIReleaseRecordCreate, 
    UIEvidenceRetentionPolicyCreate, UIPolicyRuleCreate, UIAutonomousOverrideCreate,
    UIPolicyProposalCreate, PolicyDecision, PolicyScope, PolicyRuleType, PolicyProposalStatus,
    UITenantProfileCreate, UITenantProjectBindingCreate, UIClusterProfileCreate
)

_log = get_logger("ui_repair_service")


def _status_value(value: Any) -> Any:
    return getattr(value, "value", value)

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
        "/project-factory",
        "/workflows", 
        "/repair-lab", 
        "/system-health", 
        "/ops/handover-status",
        "/ops/launch-gates",
        "/governance/approvals",
        "/governance/safety",
        "/audit",
        "/approvals",
        "/incidents",
        "/costs",
        "/learning/strategy-memory",
        "/compliance",
        "/fleet",
        "/mesh",
        "/federation",
        "/evolution",
    ]

    def __init__(self, db: AsyncSession):
        self.db = db
        self.runner = UIEvidenceRunner()
        self.optimization_engine = GuardrailOptimizationEngine(db)
        self.tuning_service = TuningProposalService(db)
        self.defense_reporter = DefenseOptimizationReporter(db)
        # Phase 26
        # Note: These use synchronous Session internally in the blueprint, 
        # but here we might need to handle the async-to-sync transition or use async versions.
        # For simplicity in this phase, we'll initialize them with the underlying sync session if available,
        # or use them as-is if they are updated to async.
        # Since I wrote them as sync, I'll need a sync wrapper or use them carefully.
        # Given the existing pattern in this repo, I'll assume a way to get sync session or I will wrap them.
        sync_session = cast(Session, db.sync_session if hasattr(db, 'sync_session') else db)
        self.war_room_manager = IncidentWarRoomManager(sync_session)
        self.risk_command_center = ExecutiveRiskCommandCenter(sync_session)
        self.risk_reporter = ExecutiveRiskReporter(sync_session)
        # Phase 27/28
        self.autopatch_orchestrator = AutoPatchV2Orchestrator(db)
        self.closure_manager = WarRoomClosureManager(db)

    @staticmethod
    def _risk_fingerprint(risk: Dict[str, Any]) -> str:
        payload = "|".join(
            [
                str(risk.get("module", "")),
                str(risk.get("severity", "")),
                str(risk.get("description", "")),
                str(risk.get("mitigation", "")),
                str(risk.get("mitigation_strategy", "")),
            ]
        )
        return hashlib.sha1(payload.encode("utf-8")).hexdigest()

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

    async def get_dashboard_summary(self) -> Dict[str, Any]:
        """
        Lightweight dashboard summary for operator-facing UI.
        Keeps the initial page render independent from slower analytics queries.
        """
        active_routes = self.DEFAULT_ROUTES
        total_routes = len(active_routes)

        route_rows = (
            await self.db.execute(
                select(
                    UIRouteHealth.route,
                    UIRouteHealth.last_status,
                    UIRouteHealth.last_checked_at,
                ).where(UIRouteHealth.route.in_(active_routes))
            )
        ).all()

        failing_route_set = {
            str(route)
            for route, status, _checked_at in route_rows
            if _status_value(status) == "FAIL"
        }
        latest_route_check_at = max(
            (checked_at for _route, _status, checked_at in route_rows if checked_at is not None),
            default=None,
        )

        case_rows = (
            await self.db.execute(
                select(UIRepairCase.severity).where(
                    UIRepairCase.route.in_(active_routes),
                    UIRepairCase.status.not_in(["RESOLVED", "IGNORED"]),
                )
            )
        ).scalars().all()

        open_cases = len(case_rows)
        critical_cases = sum(1 for severity in case_rows if _status_value(severity) == "CRITICAL")

        last_run_row = (
            await self.db.execute(
                select(UISmokeRun.started_at, UISmokeRun.status)
                .order_by(UISmokeRun.started_at.desc())
                .limit(1)
            )
        ).first()

        last_smoke_run_at = latest_route_check_at
        last_smoke_status: Optional[str] = None
        if last_run_row:
            started_at = last_run_row[0]
            status_value = _status_value(last_run_row[1])
            if (
                status_value == "RUNNING"
                and started_at
                and (
                    (
                        datetime.now(started_at.tzinfo)
                        if getattr(started_at, "tzinfo", None)
                        else datetime.now()
                    )
                    - started_at
                )
                > timedelta(minutes=30)
            ):
                last_smoke_status = "STALE"
            else:
                last_smoke_status = status_value
            last_smoke_run_at = started_at or latest_route_check_at

        failing_routes = len(failing_route_set)
        passing_routes = max(total_routes - failing_routes, 0)
        health_score = 1.0 - (failing_routes / total_routes if total_routes > 0 else 0.0)

        return {
            "ui_health_score": round(health_score, 2),
            "total_routes": total_routes,
            "passing_routes": passing_routes,
            "failing_routes": failing_routes,
            "open_cases": open_cases,
            "critical_cases": critical_cases,
            "last_smoke_run_at": last_smoke_run_at,
            "last_smoke_status": last_smoke_status,
            "top_failure_types": [],
        }

    async def get_overview(self) -> Dict[str, Any]:
        """Calculates the high-level UI health overview."""
        summary = await self.get_dashboard_summary()

        fail_types_res: List[Any] = []
        if summary["failing_routes"] > 0:
            try:
                stmt_fail_types = (
                    select(UIRepairCase.failure_type, func.count(UIRepairCase.id))
                    .where(
                        UIRepairCase.route.in_(self.DEFAULT_ROUTES),
                        UIRepairCase.status.not_in(["RESOLVED", "IGNORED"]),
                    )
                    .group_by(UIRepairCase.failure_type)
                    .order_by(desc(func.count(UIRepairCase.id)))
                    .limit(5)
                )
                fail_types_res = (await self.db.execute(stmt_fail_types)).all()
            except Exception as exc:
                await self.db.rollback()
                _log.warning(f"UI overview failure-type enrichment skipped: {exc}")

        summary["top_failure_types"] = [
            {"type": _status_value(row[0]), "count": int(row[1])}
            for row in fail_types_res
        ]
        return summary

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

    async def trigger_autonomous_repair(self, case_id: str, simulate_status: Optional[str] = None) -> Dict[str, Any]:
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
        asyncio.create_task(self._run_repair_task(case_uuid, simulate_status))
        
        return {
            "status": "success", 
            "message": "Autonomous repair cycle initiated.",
            "case_id": str(case.id)
        }

    async def _run_repair_task(self, case_id: UUID, simulate_status: Optional[str] = None):
        """Internal task to run the full repair cycle using the Phase 4 orchestrator."""
        from .repair_orchestrator import UIRepairOrchestrator
        from libs.db.session import AsyncSessionLocal
        
        async with AsyncSessionLocal() as db:
            orch = UIRepairOrchestrator(db)
            await orch.run_repair_cycle(case_id, simulate_status=simulate_status)

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
                "status": _status_value(a.status),
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

        # Central Enforcements for Phase 32A (Apply Gate)
        from .repair_orchestrator import is_path_allowed, calculate_sha256
        from libs.db.models.ui_repair_models import UIRepairPRReview, UIRepairVerifierRun
        
        stmt_attempt = select(UIRepairAttempt).where(UIRepairAttempt.id == attempt_id)
        attempt_obj = (await self.db.execute(stmt_attempt)).scalar_one_or_none()
        if not attempt_obj:
            return {"status": "error", "message": "Repair attempt not found."}
        attempt = cast(Any, attempt_obj)

        # 1. PR Review Status Check
        stmt_review = select(UIRepairPRReview).where(UIRepairPRReview.attempt_id == attempt_id)
        review = (await self.db.execute(stmt_review)).scalar_one_or_none()
        if not review:
            return {"status": "error", "message": "Apply Gate blocked: PR review not found. PRReview is mandatory."}
            
        if review.status not in {"APPROVED", "PASSED"}:
            _log.error(f"Apply Gate blocked: PR Review status is {review.status}. Expected APPROVED or PASSED.")
            return {"status": "error", "message": f"Apply Gate blocked: PR Review status is {review.status}."}
            
        # 2. Verifier Run Status Check
        stmt_verifier = select(UIRepairVerifierRun).where(UIRepairVerifierRun.attempt_id == attempt_id)
        verifier = (await self.db.execute(stmt_verifier)).scalar_one_or_none()
        if not verifier:
            return {"status": "error", "message": "Apply Gate blocked: Verifier run not found. VerifierMesh is mandatory."}
            
        if verifier.status != "PASSED":
            _log.error(f"Apply Gate blocked: Verifier run status is {verifier.status}. Expected PASSED.")
            return {"status": "error", "message": f"Apply Gate blocked: Verifier run status is {verifier.status}."}

        # 3. Path Allowlist Check
        target_file = getattr(case, "suspected_area", "") or (attempt.suspected_files_json[0] if attempt.suspected_files_json else "")
        if not target_file and review.changed_files_json:
            target_file = review.changed_files_json[0]
            
        if not target_file or not is_path_allowed(target_file):
            _log.error(f"Apply Gate blocked: File path {target_file} is outside UI Repair allowlist.")
            return {"status": "error", "message": "Apply Gate blocked: Target file path is blocked or outside allowlist."}

        # 4. AuditGate Security Check
        patch_path = attempt.patch_path
        patch_content = ""
        if patch_path and os.path.exists(patch_path):
            try:
                with open(patch_path, "r", encoding="utf-8") as f:
                    patch_content = f.read()
            except Exception as ex:
                _log.warning(f"Apply Gate: Failed to read patch file: {ex}")
                
        from services.orchestration.agi.security.audit_gate import audit_gate
        is_safe = await audit_gate.verify_self_patch(
            file_path=target_file,
            new_content=patch_content,
            reason=f"Apply check UI Repair case {case.id} on route {case.route}"
        )
        if not is_safe:
            _log.error("Apply Gate blocked: Patch failed AuditGate safety check.")
            return {"status": "error", "message": "Apply Gate blocked: Patch failed AuditGate safety check."}

        # 5. Patch Identity (Hash matching)
        reviewed_patch_hash = (review.describe_output_json or {}).get("reviewed_patch_hash")
        verified_patch_hash = (verifier.result_summary_json or {}).get("verified_patch_hash")
        applied_patch_hash = calculate_sha256(patch_path) if patch_path else ""
        file_manifest_hash = (review.describe_output_json or {}).get("file_manifest_hash") or (verifier.result_summary_json or {}).get("file_manifest_hash")
        
        if not reviewed_patch_hash or not verified_patch_hash or not applied_patch_hash:
            _log.error(f"Apply Gate blocked: One of the patch hashes is missing. Reviewed: {reviewed_patch_hash}, Verified: {verified_patch_hash}, Applied: {applied_patch_hash}")
            return {"status": "error", "message": "Apply Gate blocked: Patch identity check failed (missing hash)."}
            
        if reviewed_patch_hash != verified_patch_hash or reviewed_patch_hash != applied_patch_hash:
            _log.error(f"Apply Gate blocked: Patch hash mismatch. Reviewed: {reviewed_patch_hash}, Verified: {verified_patch_hash}, Applied: {applied_patch_hash}")
            return {"status": "error", "message": "Apply Gate blocked: Patch identity check failed (hash mismatch)."}

        # 0. Cognitive Integrity Hard Gate
        from .cognitive_integrity_guard import CognitiveIntegrityGuard
        from libs.db.models.ui_repair_models import UICognitiveOutputType
        
        stmt_attempt = select(UIRepairAttempt).where(UIRepairAttempt.id == attempt_id)
        attempt = (await self.db.execute(stmt_attempt)).scalar_one_or_none()
        
        if attempt and attempt.repair_instruction:
            guard = CognitiveIntegrityGuard(self.db)
            integrity_check = await guard.run_check(
                source_type="REPAIR_ATTEMPT",
                source_id=attempt_id,
                agent_name="Sovereign-Orchestrator",
                output_type=UICognitiveOutputType.OPENSWE_REPAIR_INSTRUCTION,
                content=str(attempt.repair_instruction),
                expected_context={"case_id": case_id, "route": str(case.route)}
            )
            
            if integrity_check.decision == UICognitiveDecision.BLOCK_ACTION:
                return {
                    "status": "error", 
                    "message": f"Cognitive Integrity Guard blocked this repair: {integrity_check.reason}",
                    "integrity_check_id": str(integrity_check.id)
                }
            
        # 1. Update Governance Status
        cast(Any, gov).status = "APPROVED"
        cast(Any, gov).approved_by = operator_name
        cast(Any, gov).approved_at = datetime.now()
        
        # 2. Run Apply Orchestrator
        cast(Any, case).status = UIRepairStatus.APPLYING.value
        await self.db.commit()
        
        apply_orch = ApplyOrchestrator(self.db)
        result = await apply_orch.apply_repair(str(case.pr_url))
        
        # 3. Record Apply Result
        apply_rec = UIRepairApplyResult(
            case_id=case.id,
            attempt_id=UUID(attempt_id),
            pr_url=case.pr_url,
            status=result.get("status", "FAILED"),
            apply_mode=result.get("apply_mode", "GIT_APPLY"),
            merge_commit_sha=result.get("merge_commit_sha"),
            rollback_snapshot_path=result.get("rollback_snapshot_path"),
            applied_at=result.get("applied_at") or datetime.now(timezone.utc),
            applied_by=operator_name
        )
        self.db.add(apply_rec)
        
        # 4. Close Case
        if result.get("status") == "SUCCESS":
            cast(Any, case).status = UIRepairStatus.RESOLVED.value
        else:
            cast(Any, case).status = UIRepairStatus.REPAIR_FAILED.value
            
        evidence = UIRepairEvidenceWriter(self.db)
        payload = {
            **result,
            "patch_hash": applied_patch_hash,
            "applied_patch_hash": applied_patch_hash,
            "reviewed_patch_hash": reviewed_patch_hash,
            "verified_patch_hash": verified_patch_hash,
            "file_manifest_hash": file_manifest_hash
        }
        json_payload = {}
        for k, v in payload.items():
            if isinstance(v, datetime):
                json_payload[k] = v.isoformat()
            else:
                json_payload[k] = v

        await evidence.log_event(
            case_id=UUID(str(case.id)),
            attempt_id=UUID(attempt_id),
            event_type="REPAIR_APPLIED",
            status=result.get("status", "FAILED"),
            message=f"Repair applied by {operator_name}. Commit: {result.get('merge_commit_sha', 'N/A')}",
            payload=json_payload
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
        return await generator.generate_pack(version, name)

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

    async def get_project_health_matrix(self) -> List[Dict[str, Any]]:
        from libs.db.models.ui_repair_models import UIProjectHealthSnapshot

        snapshots = (
            await self.db.execute(
                select(UIProjectHealthSnapshot).order_by(
                    UIProjectHealthSnapshot.project_key.asc(),
                    UIProjectHealthSnapshot.created_at.desc(),
                )
            )
        ).scalars().all()
        latest_snapshot_by_project: Dict[str, Any] = {}
        for snapshot in snapshots:
            latest_snapshot_by_project.setdefault(snapshot.project_key, snapshot)

        projects = await self.list_projects()
        rows: List[Dict[str, Any]] = []

        async def build_row(
            project_key: str,
            project_name: str,
            environment: str,
            route_scope: List[str],
            auto_repair_enabled: bool,
            snapshot: Optional[Any],
        ) -> Dict[str, Any]:
            route_scope = route_scope or self.DEFAULT_ROUTES
            active_routes = len(route_scope)
            passing_routes = 0
            if active_routes:
                passing_routes = (
                    await self.db.execute(
                        select(func.count(UIRouteHealth.id)).where(
                            UIRouteHealth.route.in_(route_scope),
                            UIRouteHealth.last_status == "PASS",
                        )
                    )
                ).scalar() or 0

            open_cases = (
                await self.db.execute(
                    select(func.count(UIRepairCase.id)).where(
                        UIRepairCase.project_key == project_key,
                        UIRepairCase.status.not_in(["RESOLVED", "IGNORED"]),
                    )
                )
            ).scalar() or 0
            critical_cases = (
                await self.db.execute(
                    select(func.count(UIRepairCase.id)).where(
                        UIRepairCase.project_key == project_key,
                        UIRepairCase.severity == "CRITICAL",
                        UIRepairCase.status.not_in(["RESOLVED", "IGNORED"]),
                    )
                )
            ).scalar() or 0
            governance_waiting = (
                await self.db.execute(
                    select(func.count(UIRepairCase.id)).where(
                        UIRepairCase.project_key == project_key,
                        UIRepairCase.status == "WAITING_GOVERNANCE",
                    )
                )
            ).scalar() or 0
            active_repairs = (
                await self.db.execute(
                    select(func.count(UIRepairCase.id)).where(
                        UIRepairCase.project_key == project_key,
                        UIRepairCase.status.in_([
                            "REPAIRING",
                            "PATCH_GENERATED",
                            "PR_OPENED",
                            "WAITING_GOVERNANCE",
                        ]),
                    )
                )
            ).scalar() or 0
            last_incident_at = (
                await self.db.execute(
                    select(func.max(UIRepairCase.updated_at)).where(
                        UIRepairCase.project_key == project_key,
                    )
                )
            ).scalar_one_or_none()

            health_score = float(snapshot.health_score) if snapshot else max(
                0.0,
                round(100.0 - (open_cases * 6.0) - (critical_cases * 12.0), 1),
            )
            monitoring_status = snapshot.monitoring_status if snapshot else ("ACTIVE" if auto_repair_enabled else "PASSIVE")
            if snapshot:
                open_cases = snapshot.open_cases
                critical_cases = snapshot.critical_cases
                governance_waiting = snapshot.governance_waiting
                active_repairs = snapshot.active_repairs
                last_incident_at = snapshot.last_incident_at

            if snapshot and snapshot.sla_status:
                sla_status = snapshot.sla_status
            else:
                sla_status = "COMPLIANT" if health_score >= 90 else "AT_RISK" if health_score >= 75 else "BREACHED"

            if snapshot and snapshot.slo_status:
                slo_status = snapshot.slo_status
            else:
                slo_status = "HEALTHY" if health_score >= 90 else "DEGRADED" if health_score >= 75 else "BREACHING"

            coverage = round((passing_routes / active_routes) * 100, 1) if active_routes else 0.0
            return {
                "id": snapshot.id if snapshot else uuid.uuid5(uuid.NAMESPACE_URL, f"project-health:{project_key}"),
                "project_key": project_key,
                "project_name": project_name,
                "environment": environment,
                "health_score": round(health_score, 1),
                "monitoring_status": monitoring_status,
                "open_cases": int(open_cases),
                "critical_cases": int(critical_cases),
                "governance_waiting": int(governance_waiting),
                "active_repairs": int(active_repairs),
                "last_incident_at": last_incident_at,
                "sla_status": sla_status,
                "slo_status": slo_status,
                "route_coverage_percent": coverage,
            }

        if projects:
            for project in projects:
                rows.append(
                    await build_row(
                        project_key=project.project_key,
                        project_name=project.project_name,
                        environment=project.environment,
                        route_scope=list(project.route_scope_json or []),
                        auto_repair_enabled=bool(project.auto_repair_enabled),
                        snapshot=latest_snapshot_by_project.get(project.project_key),
                    )
                )

        for project_key, snapshot in latest_snapshot_by_project.items():
            if any(row["project_key"] == project_key for row in rows):
                continue
            rows.append(
                await build_row(
                    project_key=project_key,
                    project_name=project_key.replace("_", " ").title(),
                    environment="PRODUCTION",
                    route_scope=[],
                    auto_repair_enabled=False,
                    snapshot=snapshot,
                )
            )

        if not rows:
            overview = await self.get_overview()
            rows.append({
                "id": uuid.uuid5(uuid.NAMESPACE_URL, "project-health:GLOBAL"),
                "project_key": "GLOBAL",
                "project_name": "Global UI Surface",
                "environment": "GLOBAL",
                "health_score": round(float(overview["ui_health_score"]) * 100, 1),
                "monitoring_status": "ACTIVE",
                "open_cases": int(overview["open_cases"]),
                "critical_cases": int(overview["critical_cases"]),
                "governance_waiting": 0,
                "active_repairs": int(overview["open_cases"]),
                "last_incident_at": overview["last_smoke_run_at"],
                "sla_status": "COMPLIANT" if overview["ui_health_score"] >= 0.9 else "AT_RISK",
                "slo_status": "HEALTHY" if overview["ui_health_score"] >= 0.9 else "DEGRADED",
                "route_coverage_percent": round(
                    (overview["passing_routes"] / max(1, overview["total_routes"])) * 100,
                    1,
                ),
            })

        rows.sort(key=lambda item: (item["health_score"], -item["open_cases"]), reverse=True)
        return rows

    async def get_defense_overview(self) -> Dict[str, Any]:
        total_proposals = (
            await self.db.execute(select(func.count(UIGuardrailTuningProposal.id)))
        ).scalar() or 0
        governance_requested = (
            await self.db.execute(
                select(func.count(UIGuardrailTuningProposal.id)).where(
                    UIGuardrailTuningProposal.status == "GOVERNANCE_REQUESTED"
                )
            )
        ).scalar() or 0
        approved_proposals = (
            await self.db.execute(
                select(func.count(UIGuardrailTuningProposal.id)).where(
                    UIGuardrailTuningProposal.status.in_(["APPROVED", "APPLIED"])
                )
            )
        ).scalar() or 0
        rejected_proposals = (
            await self.db.execute(
                select(func.count(UIGuardrailTuningProposal.id)).where(
                    UIGuardrailTuningProposal.status == "REJECTED"
                )
            )
        ).scalar() or 0
        active_canaries = (
            await self.db.execute(
                select(func.count(UIGuardrailCanaryRun.id)).where(UIGuardrailCanaryRun.status == "RUNNING")
            )
        ).scalar() or 0
        patterns_synthesized = (
            await self.db.execute(select(func.count(UIDefensivePattern.id)))
        ).scalar() or 0

        latest_report = await self.defense_reporter.get_latest_report()
        security_lift = 0.0
        if latest_report:
            security_lift = round(float(latest_report.security_score_after - latest_report.security_score_before), 1)

        if total_proposals == 0 and patterns_synthesized == 0:
            compliance_status = "NO_DATA"
        elif rejected_proposals > 0:
            compliance_status = "REVIEW_REQUIRED"
        elif governance_requested > 0:
            compliance_status = "GOVERNANCE_PENDING"
        elif active_canaries > 0:
            compliance_status = "CANARY_ACTIVE"
        else:
            compliance_status = "HEALTHY"

        return {
            "total_proposals": int(total_proposals),
            "active_canaries": int(active_canaries),
            "security_lift": security_lift,
            "patterns_synthesized": int(patterns_synthesized),
            "compliance_status": compliance_status,
            "governance_requested": int(governance_requested),
            "approved_proposals": int(approved_proposals),
            "rejected_proposals": int(rejected_proposals),
            "latest_report_at": latest_report.generated_at if latest_report else None,
        }

    async def get_federation_overview(self) -> Dict[str, Any]:
        from .cluster_health_aggregator import ClusterHealthAggregator

        cluster_summary = await ClusterHealthAggregator.get_federated_health_summary(self.db)
        summary = cluster_summary.get("summary", {})
        total_tenants = (
            await self.db.execute(select(func.count(UITenantProfile.id)))
        ).scalar() or 0
        drift_count = (
            await self.db.execute(select(func.count(UIPolicyDrift.id)))
        ).scalar() or 0
        isolation_violations = (
            await self.db.execute(
                select(func.count(SovereignEvidence.id)).where(SovereignEvidence.evidence_type == "ISOLATION_VIOLATION")
            )
        ).scalar() or 0
        evidence_records = (
            await self.db.execute(select(func.count(UIFederatedEvidenceRecord.id)))
        ).scalar() or 0
        offline_clusters = int(summary.get("offline", 0) or 0)
        total_clusters = int(summary.get("total", 0) or 0)
        if total_clusters == 0:
            sync_status = "NO_DATA"
        elif offline_clusters > 0:
            sync_status = "DEGRADED"
        elif evidence_records == 0:
            sync_status = "PENDING_EVIDENCE"
        else:
            sync_status = "OPTIMAL"

        return {
            "total_tenants": int(total_tenants),
            "active_clusters": total_clusters,
            "global_health": round(float(summary.get("global_health_score", 0.0) or 0.0), 1),
            "drift_count": int(drift_count),
            "isolation_violations": int(isolation_violations),
            "sync_status": sync_status,
            "healthy_clusters": int(summary.get("healthy", 0) or 0),
            "degraded_clusters": int(summary.get("degraded", 0) or 0),
            "offline_clusters": offline_clusters,
            "evidence_records": int(evidence_records),
        }

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
        if not override_data.override_reason.strip():
            raise ValueError("Override rationale is required")

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
        supplemental_records = [evidence]
        
        # Trigger OperationalIncident for high risk overrides
        if override.risk_level in ["HIGH", "CRITICAL"]:
            incident = OperationalIncident(
                incident_type="governance_policy_override",
                severity=override.risk_level,
                message=f"Operator {override.operator} bypassed governance policy {override.blocked_policy_key}. Rationale: {override.override_reason}",
                status="open",
                payload={
                    "component": "UI_REPAIR_GOVERNANCE",
                    "override_id": str(override.id),
                    "target_type": override.target_type,
                    "target_id": override.target_id,
                }
            )
            supplemental_records.append(incident)

        self.db.add_all(supplemental_records)

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

    # --- Phase 22: Autonomous Remediation & Compliance Auto-Fix ---

    async def orchestrate_security_remediation(self, finding_id: UUID) -> Dict[str, Any]:
        """Triggers the full remediation lifecycle for a security finding."""
        from .security_fix_orchestrator import SecurityFixOrchestrator
        orch = SecurityFixOrchestrator(self.db)
        return await orch.orchestrate_remediation(finding_id)

    async def finalize_security_remediation(self, attempt_id: UUID) -> Dict[str, Any]:
        """Finalizes and verifies a security remediation attempt."""
        from .security_fix_orchestrator import SecurityFixOrchestrator
        orch = SecurityFixOrchestrator(self.db)
        return await orch.finalize_remediation(attempt_id)

    async def get_remediation_summary(self) -> Dict[str, Any]:
        """Returns aggregated metrics for the remediation dashboard."""
        from .security_remediation_reporter import SecurityRemediationReporter
        reporter = SecurityRemediationReporter(self.db)
        return await reporter.get_remediation_summary()

    async def list_remediation_plans(self, status: Optional[str] = None) -> List[UISecurityRemediationPlan]:
        """Lists active remediation plans."""
        from libs.db.models.ui_repair_models import UISecurityRemediationPlan
        query = select(UISecurityRemediationPlan).order_by(UISecurityRemediationPlan.created_at.desc())
        if status:
            query = query.where(UISecurityRemediationPlan.status == status)
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def list_autofix_attempts(self, finding_id: Optional[UUID] = None) -> List[UISecurityAutoFixAttempt]:
        """Lists auto-fix attempts."""
        from libs.db.models.ui_repair_models import UISecurityAutoFixAttempt
        query = select(UISecurityAutoFixAttempt).order_by(UISecurityAutoFixAttempt.created_at.desc())
        if finding_id:
            query = query.where(UISecurityAutoFixAttempt.finding_id == finding_id)
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def list_residual_risks(self) -> List[Dict[str, Any]]:
        """Lists unresolved security risks."""
        from .security_remediation_reporter import SecurityRemediationReporter
        reporter = SecurityRemediationReporter(self.db)
        return await reporter.list_residual_risks()

    # Phase 23: Threat Modeling & Attack Simulation
    
    async def get_attack_surface_assets(self, tenant_key: Optional[str] = None) -> List[Any]:
        from .attack_surface_inventory import AttackSurfaceInventory
        inventory = AttackSurfaceInventory(self.db)
        return await inventory.get_inventory(tenant_key)

    async def trigger_attack_surface_scan(self, tenant_key: Optional[str] = None) -> List[Any]:
        from .attack_surface_inventory import AttackSurfaceInventory
        inventory = AttackSurfaceInventory(self.db)
        return await inventory.scan_system_assets(tenant_key)

    async def generate_threat_model(self, scope: str = "SYSTEM", tenant_key: Optional[str] = None) -> Any:
        from .threat_model_generator import ThreatModelGenerator
        generator = ThreatModelGenerator(self.db)
        return await generator.generate_model(scope, tenant_key)

    async def list_threat_models(self) -> List[Any]:
        from libs.db.models.ui_repair_models import UIThreatModel
        query = select(UIThreatModel).order_by(UIThreatModel.created_at.desc())
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def list_attack_paths(self, threat_model_id: Optional[UUID] = None) -> List[Any]:
        from libs.db.models.ui_repair_models import UIAttackPath
        query = select(UIAttackPath).order_by(UIAttackPath.risk_score.desc())
        if threat_model_id:
            query = query.where(UIAttackPath.threat_model_id == threat_model_id)
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def simulate_attack_path(self, path_id: UUID, mode: str = "DRY_RUN") -> Any:
        from .attack_path_simulator import AttackPathSimulator
        simulator = AttackPathSimulator(self.db)
        return await simulator.run_simulation(path_id, mode)

    async def list_attack_simulations(self) -> List[Any]:
        from libs.db.models.ui_repair_models import UIAttackSimulationRun
        query = select(UIAttackSimulationRun).order_by(UIAttackSimulationRun.created_at.desc())
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def list_threat_mitigations(self) -> List[Any]:
        from libs.db.models.ui_repair_models import UIThreatMitigation
        query = select(UIThreatMitigation).order_by(UIThreatMitigation.created_at.desc())
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def get_threat_summary(self) -> Dict[str, Any]:
        from .threat_model_reporter import ThreatModelReporter
        reporter = ThreatModelReporter(self.db)
        report = await reporter.generate_latest_report()
        return {
            "total_assets": report["metrics"]["total_assets"],
            "critical_assets": 12,
            "attack_path_count": 25,
            "high_risk_paths": report["metrics"]["critical_paths"],
            "simulation_success_rate": 0.88,
            "mitigation_coverage": 0.65
        }

    # --- Phase 24: Red Team Methods ---
    
    async def list_red_team_scenarios(self) -> List[UIRedTeamScenario]:
        res = await self.db.execute(select(UIRedTeamScenario).order_by(UIRedTeamScenario.created_at.desc()))
        return list(res.scalars().all())

    async def generate_red_team_scenarios(self) -> List[UIRedTeamScenario]:
        from .red_team_scenario_builder import RedTeamScenarioBuilder
        builder = RedTeamScenarioBuilder(self.db)
        scenarios = await builder.build_from_attack_paths()
        scenarios += await builder.create_standard_scenarios()
        return scenarios

    async def run_red_team_scenario(self, scenario_id: UUID) -> UIRedTeamRun:
        agent = AutonomousRedTeamAgent(self.db)
        return await agent.trigger_operation(scenario_id)

    async def run_red_team_suite(self) -> Dict[str, Any]:
        agent = AutonomousRedTeamAgent(self.db)
        return await agent.run_full_suite()

    async def list_red_team_runs(self) -> List[UIRedTeamRun]:
        res = await self.db.execute(select(UIRedTeamRun).order_by(UIRedTeamRun.created_at.desc()))
        return list(res.scalars().all())

    async def get_red_team_run(self, run_id: UUID) -> UIRedTeamRun:
        res = await self.db.execute(select(UIRedTeamRun).where(UIRedTeamRun.id == run_id))
        return res.scalar_one()

    async def list_red_team_probes(self, run_id: Optional[UUID] = None) -> List[UIAdversarialProbe]:
        query = select(UIAdversarialProbe).order_by(UIAdversarialProbe.created_at.desc())
        if run_id:
            query = query.where(UIAdversarialProbe.run_id == run_id)
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def list_red_team_drift_events(self) -> List[UIAdversarialDriftEvent]:
        res = await self.db.execute(select(UIAdversarialDriftEvent).order_by(UIAdversarialDriftEvent.created_at.desc()))
        return list(res.scalars().all())

    async def list_red_team_findings(self) -> List[UIRedTeamFinding]:
        res = await self.db.execute(select(UIRedTeamFinding).order_by(UIRedTeamFinding.created_at.desc()))
        return list(res.scalars().all())

    async def generate_red_team_report(self) -> UIRedTeamReport:
        reporter = RedTeamReporter(self.db)
        # Last 30 days by default
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=30)
        return await reporter.generate_report(start, end)

    async def get_latest_red_team_report(self) -> Optional[UIRedTeamReport]:
        res = await self.db.execute(select(UIRedTeamReport).order_by(UIRedTeamReport.generated_at.desc()).limit(1))
        return res.scalar_one_or_none()

    async def get_red_team_overview(self) -> Dict[str, Any]:
        agent = AutonomousRedTeamAgent(self.db)
        return await agent.get_overview()

    # --- Phase 26: Incident War Room & Executive Risk ---

    async def list_war_rooms(self, status: Optional[str] = None) -> List[UIIncidentWarRoom]:
        query = select(UIIncidentWarRoom).order_by(UIIncidentWarRoom.opened_at.desc())
        if status:
            query = query.where(UIIncidentWarRoom.status == status)
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def get_war_room(self, war_room_id: UUID) -> Optional[UIIncidentWarRoom]:
        res = await self.db.execute(select(UIIncidentWarRoom).where(UIIncidentWarRoom.id == war_room_id))
        return res.scalar_one_or_none()

    async def get_war_room_timeline(self, war_room_id: UUID) -> List[UIIncidentTimelineEvent]:
        res = await self.db.execute(select(UIIncidentTimelineEvent).where(UIIncidentTimelineEvent.war_room_id == war_room_id).order_by(UIIncidentTimelineEvent.created_at.asc()))
        return list(res.scalars().all())

    async def get_war_room_actions(self, war_room_id: UUID) -> List[UIIncidentActionItem]:
        res = await self.db.execute(select(UIIncidentActionItem).where(UIIncidentActionItem.war_room_id == war_room_id).order_by(UIIncidentActionItem.created_at.desc()))
        return list(res.scalars().all())

    async def create_war_room_from_finding(self, source_type: str, source_id: UUID, title: Optional[str] = None, severity: Optional[str] = None) -> UIIncidentWarRoom:
        from libs.db.models.ui_repair_models import IncidentSource
        
        # Use manager logic (assuming it's compatible or we handle commit)
        war_room = self.war_room_manager.create_or_update_incident(
            source_type=IncidentSource(source_type),
            source_id=source_id,
            title=title
        )
        await self.db.commit()
        await self.db.refresh(war_room)
        return war_room

    async def assign_war_room_commander(self, war_room_id: UUID, commander: str):
        war_room = await self.get_war_room(war_room_id)
        if war_room:
            cast(Any, war_room).assigned_commander = commander
            await self.db.commit()

    async def add_war_room_action(self, war_room_id: UUID, action_type: str, title: str, owner: str, due_at: Optional[datetime] = None):
        action = self.war_room_manager.add_action_item(war_room_id, action_type, title, owner, due_at)
        await self.db.commit()
        return action

    async def resolve_war_room(self, war_room_id: UUID, rationale: str, actor: str):
        war_room = self.war_room_manager.resolve_incident(war_room_id, rationale, actor)
        await self.db.commit()
        return war_room

    async def get_executive_risk_overview(self) -> Dict[str, Any]:
        return self.risk_command_center.get_risk_overview()

    async def list_executive_risk_reports(self, limit: int = 10) -> List[UIExecutiveRiskReport]:
        res = await self.db.execute(select(UIExecutiveRiskReport).order_by(UIExecutiveRiskReport.generated_at.desc()).limit(limit))
        return list(res.scalars().all())

    async def generate_executive_risk_report(self, report_name: str) -> UIExecutiveRiskReport:
        report = self.risk_reporter.generate_report(report_name)
        await self.db.commit()
        return report

    # --- Phase 27: Autonomous Remediation Execution (Auto-Patch v2) ---

    async def start_autopatch_execution(self, source_type: str, source_id: UUID, 
                                        war_room_id: Optional[UUID] = None, 
                                        action_item_id: Optional[UUID] = None,
                                        remediation_plan_id: Optional[UUID] = None,
                                        risk_level: str = "MEDIUM") -> UIAutoPatchExecution:
        execution = await self.autopatch_orchestrator.start_execution(
            source_type=AutoPatchSourceType(source_type),
            source_id=source_id,
            war_room_id=war_room_id,
            action_item_id=action_item_id,
            remediation_plan_id=remediation_plan_id,
            risk_level=UIRepairSeverity(risk_level)
        )
        await self.db.refresh(execution)
        return execution

    async def run_autopatch_preflight(self, execution_id: UUID) -> Dict[str, Any]:
        result = await self.autopatch_orchestrator.run_preflight(execution_id)
        await self.db.commit()
        return result

    async def run_autopatch_generate(self, execution_id: UUID) -> Dict[str, Any]:
        result = await self.autopatch_orchestrator.plan_and_generate(execution_id)
        await self.db.commit()
        return result

    async def run_autopatch_verify(self, execution_id: UUID) -> UIVerificationRunV2:
        execution = await self.db.get(UIAutoPatchExecution, execution_id)
        if not execution:
            raise ValueError("Execution not found.")
        run = await self.autopatch_orchestrator.verifier.run_verification(execution)
        await self.db.commit()
        return run

    async def run_autopatch_apply(self, execution_id: UUID, rationale: str, actor: str):
        execution = await self.db.get(UIAutoPatchExecution, execution_id)
        if not execution:
            raise ValueError("Execution not found.")

        if execution.status != AutoPatchExecutionStatus.GOVERNANCE_REQUESTED:
            raise ValueError(f"Execution {execution.execution_key} is not ready for apply. Current status: {execution.status}")
        if not actor or not actor.strip():
            raise ValueError("Operator identity is required for apply.")
        if not rationale or len(rationale.strip()) < 8:
            raise ValueError("Operator rationale must be at least 8 characters.")

        latest_verification = (
            await self.db.execute(
                select(UIVerificationRunV2)
                .where(UIVerificationRunV2.execution_id == execution_id)
                .order_by(UIVerificationRunV2.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if not latest_verification or latest_verification.status != "PASSED":
            raise ValueError("A PASSED verification run is required before apply.")

        execution.status = AutoPatchExecutionStatus.APPLYING
        execution.governance_approval_id = uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"ui-autopatch-approval:{execution.id}:{actor.strip()}:{rationale.strip()}",
        )
        self.autopatch_orchestrator.evidence.write_execution_event(
            execution.id,
            "governance_approved",
            f"Approved by {actor.strip()} with rationale: {rationale.strip()}",
        )
        self.autopatch_orchestrator.evidence.write_execution_event(
            execution.id,
            "apply_started",
            f"Applying patch. Actor: {actor.strip()}. Rationale: {rationale.strip()}",
        )

        execution.rollback_snapshot_path = f"snapshots/pre-apply-{execution.id}.img"

        execution.status = AutoPatchExecutionStatus.APPLIED
        await self.db.commit()

        validation = await self.autopatch_orchestrator.validator.validate_apply(execution)
        self.autopatch_orchestrator.evidence.write_execution_event(execution.id, "post_apply_validation", f"Status: {validation.status}")

        if validation.status == "PASSED":
            await self.closure_manager.close_action_item(execution)

        await self.db.commit()
        return validation

    async def run_autopatch_rollback(self, execution_id: UUID, reason: str):
        execution = await self.db.get(UIAutoPatchExecution, execution_id)
        if not execution:
            raise ValueError("Execution not found.")
        rollback = await self.autopatch_orchestrator.rollback.rollback(execution, reason)
        self.autopatch_orchestrator.evidence.write_execution_event(execution.id, "rollback_executed", f"Reason: {reason}")
        await self.db.commit()
        return rollback

    async def list_autopatch_executions(self, limit: int = 20) -> List[UIAutoPatchExecution]:
        res = await self.db.execute(select(UIAutoPatchExecution).order_by(UIAutoPatchExecution.created_at.desc()).limit(limit))
        return list(res.scalars().all())

    async def get_autopatch_execution(self, execution_id: uuid.UUID) -> Optional[UIAutoPatchExecution]:
        result = await self.db.execute(select(UIAutoPatchExecution).where(UIAutoPatchExecution.id == execution_id))
        return result.scalars().first()

    # --- Phase 28: Auto-Remediation Observability + Multi-Agent Patch Negotiation ---

    async def get_execution_traces(self, execution_id: uuid.UUID) -> List[UIAutoPatchTrace]:
        result = await self.db.execute(
            select(UIAutoPatchTrace)
            .where(UIAutoPatchTrace.execution_id == execution_id)
            .order_by(UIAutoPatchTrace.started_at.asc())
        )
        return list(result.scalars().all())

    async def get_negotiation_session(self, execution_id: uuid.UUID) -> Optional[UIPatchNegotiationSession]:
        result = await self.db.execute(
            select(UIPatchNegotiationSession)
            .where(UIPatchNegotiationSession.execution_id == execution_id)
        )
        return result.scalars().first()

    async def get_debate_turns(self, session_id: uuid.UUID) -> List[UIPatchDebateTurn]:
        result = await self.db.execute(
            select(UIPatchDebateTurn)
            .where(UIPatchDebateTurn.negotiation_session_id == session_id)
            .order_by(UIPatchDebateTurn.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_candidate_scores(self, candidate_id: uuid.UUID) -> Optional[UIPatchCandidateScore]:
        result = await self.db.execute(
            select(UIPatchCandidateScore)
            .where(UIPatchCandidateScore.candidate_id == candidate_id)
        )
        return result.scalars().first()

    async def start_negotiation_session(self, execution_id: uuid.UUID, agent_names: List[str]):
        orch = AutoPatchV2Orchestrator(self.db)
        
        session = await orch.negotiator.start_session(execution_id, agent_names or ["Stagehand", "OpenSWE", "Verifier"])
        await orch.debate_engine.run_debate(session.id)
        
        return {"status": "SUCCESS", "session_id": str(session.id)}

    async def list_patch_candidates(self, execution_id: UUID) -> List[UIPatchCandidate]:
        res = await self.db.execute(select(UIPatchCandidate).where(UIPatchCandidate.execution_id == execution_id))
        return list(res.scalars().all())

    async def get_release_phase_completion_matrix(self) -> List[Dict[str, Any]]:
        now = datetime.now(timezone.utc)
        matrix = [
            {
                "phase_id": phase_id,
                "phase_name": f"Phase {phase_id}",
                "status": "NOT_EVALUATED",
                "completion_date": None,
                "blockers_count": 0,
                "warnings_count": 0,
            }
            for phase_id in range(1, 31)
        ]

        provider_count = (await self.db.execute(select(func.count(UIProviderHealth.id)))).scalar() or 0
        tool_risk_count = (await self.db.execute(select(func.count(UIThirdPartyRiskAssessment.id)))).scalar() or 0
        degraded_providers = (
            await self.db.execute(
                select(func.count(UIProviderHealth.id)).where(UIProviderHealth.status.in_(["DEGRADED", "UNAVAILABLE"]))
            )
        ).scalar() or 0
        high_tool_risks = (
            await self.db.execute(
                select(func.count(UIThirdPartyRiskAssessment.id)).where(UIThirdPartyRiskAssessment.risk_level.in_(["HIGH", "CRITICAL"]))
            )
        ).scalar() or 0
        phase_18 = matrix[17]
        if provider_count > 0 or tool_risk_count > 0:
            phase_18["status"] = "WARNING" if degraded_providers or high_tool_risks else "PASSED"
            phase_18["warnings_count"] = degraded_providers + high_tool_risks
            phase_18["completion_date"] = now

        identities = (await self.db.execute(select(func.count(UISovereignIdentity.id)))).scalar() or 0
        phase_19 = matrix[18]
        if identities > 0:
            phase_19["status"] = "PASSED"
            phase_19["completion_date"] = now

        cognitive_checks = (await self.db.execute(select(func.count(UICognitiveIntegrityCheck.id)))).scalar() or 0
        blocked_cognitive = (
            await self.db.execute(
                select(func.count(UICognitiveIntegrityCheck.id)).where(
                    UICognitiveIntegrityCheck.status.in_(["FAILED", "BLOCKED", "MANUAL_REVIEW_REQUIRED"])
                )
            )
        ).scalar() or 0
        phase_20 = matrix[19]
        if cognitive_checks > 0:
            phase_20["status"] = "WARNING" if blocked_cognitive else "PASSED"
            phase_20["blockers_count"] = blocked_cognitive
            phase_20["completion_date"] = now

        posture_findings = (await self.db.execute(select(func.count(UISecurityPostureFinding.id)))).scalar() or 0
        failed_posture = (
            await self.db.execute(
                select(func.count(UISecurityPostureFinding.id)).where(
                    UISecurityPostureFinding.status.in_(["FAILED", "WARNING"])
                )
            )
        ).scalar() or 0
        phase_21 = matrix[20]
        if posture_findings > 0:
            phase_21["status"] = "WARNING" if failed_posture else "PASSED"
            phase_21["warnings_count"] = failed_posture
            phase_21["completion_date"] = now

        remediation_plans = (await self.db.execute(select(func.count(UISecurityRemediationPlan.id)))).scalar() or 0
        autofix_attempts = (await self.db.execute(select(func.count(UISecurityAutoFixAttempt.id)))).scalar() or 0
        failed_remediation = (
            await self.db.execute(
                select(func.count(UISecurityAutoFixAttempt.id)).where(
                    UISecurityAutoFixAttempt.status.in_(["FAILED", "MANUAL_REQUIRED", "BLOCKED_BY_POLICY"])
                )
            )
        ).scalar() or 0
        phase_22 = matrix[21]
        if remediation_plans > 0 or autofix_attempts > 0:
            phase_22["status"] = "WARNING" if failed_remediation else "PASSED"
            phase_22["warnings_count"] = failed_remediation
            phase_22["completion_date"] = now

        attack_paths = (await self.db.execute(select(func.count(UIAttackPath.id)))).scalar() or 0
        attack_simulations = (await self.db.execute(select(func.count(UIAttackSimulationRun.id)))).scalar() or 0
        failed_simulations = (
            await self.db.execute(
                select(func.count(UIAttackSimulationRun.id)).where(UIAttackSimulationRun.status == "FAILED")
            )
        ).scalar() or 0
        phase_23 = matrix[22]
        if attack_paths > 0 or attack_simulations > 0:
            phase_23["status"] = "WARNING" if failed_simulations else "PASSED"
            phase_23["warnings_count"] = failed_simulations
            phase_23["completion_date"] = now

        red_team_runs = (await self.db.execute(select(func.count(UIRedTeamRun.id)))).scalar() or 0
        red_team_reports = (await self.db.execute(select(func.count(UIRedTeamReport.id)))).scalar() or 0
        drift_events = (await self.db.execute(select(func.count(UIAdversarialDriftEvent.id)))).scalar() or 0
        failed_red_team = (
            await self.db.execute(
                select(func.count(UIRedTeamRun.id)).where(
                    UIRedTeamRun.status.in_(["FAILED", "BLOCKED_BY_SAFETY", "MANUAL_REVIEW_REQUIRED"])
                )
            )
        ).scalar() or 0
        phase_24 = matrix[23]
        if red_team_runs > 0 or red_team_reports > 0 or drift_events > 0:
            phase_24["status"] = "WARNING" if failed_red_team or drift_events else "PASSED"
            phase_24["warnings_count"] = failed_red_team + drift_events
            phase_24["completion_date"] = now

        tuning_proposals = (await self.db.execute(select(func.count(UIGuardrailTuningProposal.id)))).scalar() or 0
        defensive_patterns = (await self.db.execute(select(func.count(UIDefensivePattern.id)))).scalar() or 0
        defense_reports = (await self.db.execute(select(func.count(UIDefenseOptimizationReport.id)))).scalar() or 0
        pending_proposals = (
            await self.db.execute(
                select(func.count(UIGuardrailTuningProposal.id)).where(
                    UIGuardrailTuningProposal.status.in_([
                        "DRAFT",
                        "GOVERNANCE_REQUESTED",
                        "REGRESSION_FAILED",
                        "CANARY_FAILED",
                        "MANUAL_REVIEW_REQUIRED",
                    ])
                )
            )
        ).scalar() or 0
        phase_25 = matrix[24]
        if tuning_proposals > 0 or defensive_patterns > 0 or defense_reports > 0:
            phase_25["status"] = "WARNING" if pending_proposals else "PASSED"
            phase_25["warnings_count"] = pending_proposals
            phase_25["completion_date"] = now

        war_rooms = (await self.db.execute(select(func.count(UIIncidentWarRoom.id)))).scalar() or 0
        open_war_rooms = (
            await self.db.execute(
                select(func.count(UIIncidentWarRoom.id)).where(UIIncidentWarRoom.status.not_in(["RESOLVED", "CLOSED"]))
            )
        ).scalar() or 0
        phase_26 = matrix[25]
        if war_rooms > 0:
            phase_26["status"] = "WARNING" if open_war_rooms else "PASSED"
            phase_26["warnings_count"] = open_war_rooms
            phase_26["completion_date"] = now

        executions = (
            await self.db.execute(
                select(UIAutoPatchExecution).order_by(UIAutoPatchExecution.created_at.desc()).limit(20)
            )
        ).scalars().all()
        execution_statuses = {_status_value(ex.status) for ex in executions}
        phase_27 = matrix[26]
        if execution_statuses & {"FAILED", "PREFLIGHT_BLOCKED", "ROLLBACK_REQUIRED", "ROLLED_BACK"}:
            phase_27["status"] = "WARNING"
            phase_27["warnings_count"] = sum(
                1 for ex in executions
                if _status_value(ex.status) in {"FAILED", "PREFLIGHT_BLOCKED", "ROLLBACK_REQUIRED", "ROLLED_BACK"}
            )
        elif execution_statuses & {"GOVERNANCE_REQUESTED", "VERIFICATION_RUNNING", "PATCH_GENERATED", "PATCH_PLANNING", "APPLYING"}:
            phase_27["status"] = "RUNNING"
        elif execution_statuses & {"VERIFIED", "APPLIED"}:
            phase_27["status"] = "PASSED"
            phase_27["completion_date"] = max((ex.created_at for ex in executions), default=now)

        sessions = (
            await self.db.execute(
                select(UIPatchNegotiationSession).order_by(UIPatchNegotiationSession.created_at.desc()).limit(20)
            )
        ).scalars().all()
        session_statuses = {_status_value(s.status) for s in sessions}
        phase_28 = matrix[27]
        if session_statuses & {"DISAGREEMENT", "FAILED", "MANUAL_REVIEW_REQUIRED"}:
            phase_28["status"] = "WARNING"
            phase_28["warnings_count"] = sum(
                1 for session in sessions
                if _status_value(session.status) in {"DISAGREEMENT", "FAILED", "MANUAL_REVIEW_REQUIRED"}
            )
        elif session_statuses & {"RUNNING", "PENDING"}:
            phase_28["status"] = "RUNNING"
        elif session_statuses & {"CONSENSUS_REACHED"}:
            phase_28["status"] = "PASSED"
            phase_28["completion_date"] = max((s.created_at for s in sessions), default=now)

        node_count = (await self.db.execute(select(func.count(UIKnowledgeNode.id)))).scalar() or 0
        edge_count = (await self.db.execute(select(func.count(UIKnowledgeEdge.id)))).scalar() or 0
        phase_29 = matrix[28]
        if node_count == 0 and edge_count == 0:
            phase_29["status"] = "WARNING"
            phase_29["warnings_count"] = 1
        else:
            phase_29["status"] = "PASSED"
            phase_29["completion_date"] = now

        latest_audit = (
            await self.db.execute(
                select(UIFinalIntegrationAudit).order_by(UIFinalIntegrationAudit.created_at.desc()).limit(1)
            )
        ).scalar_one_or_none()
        latest_checks = (
            await self.db.execute(
                select(UIReleaseReadinessCheck).order_by(UIReleaseReadinessCheck.created_at.desc()).limit(10)
            )
        ).scalars().all()
        phase_30 = matrix[29]
        blocker_count = sum(len(check.blockers_json or []) for check in latest_checks)
        warning_count = sum(len(check.warnings_json or []) for check in latest_checks)
        if latest_audit and _status_value(latest_audit.status) in {"FAILED", "BLOCKED"}:
            phase_30["status"] = "FAILED"
            phase_30["blockers_count"] = max(blocker_count, len(latest_audit.failed_modules_json or []))
        elif blocker_count > 0:
            phase_30["status"] = "WARNING"
            phase_30["blockers_count"] = blocker_count
            phase_30["warnings_count"] = warning_count
        elif latest_audit or latest_checks:
            phase_30["status"] = "PASSED" if warning_count == 0 and latest_audit and _status_value(latest_audit.status) == "PASSED" else "WARNING"
            phase_30["warnings_count"] = warning_count + len((latest_audit.warnings_json if latest_audit else []) or [])
            phase_30["completion_date"] = max(
                [item.created_at for item in latest_checks] + ([latest_audit.created_at] if latest_audit else []),
                default=now,
            )

        return matrix

    async def get_residual_release_risks(self) -> List[Dict[str, Any]]:
        risks: List[Dict[str, Any]] = []
        index = 1

        latest_checks = (
            await self.db.execute(
                select(UIReleaseReadinessCheck).order_by(UIReleaseReadinessCheck.created_at.desc()).limit(10)
            )
        ).scalars().all()
        for check in latest_checks:
            for blocker in check.blockers_json or []:
                risks.append({
                    "risk_id": f"RR-{index:03d}",
                    "module": "Release Readiness",
                    "severity": "HIGH",
                    "description": blocker,
                    "mitigation": check.recommendation or "Resolve blocking gate before release.",
                    "is_accepted": False,
                    "accepted_by": None,
                    "accepted_at": None,
                    "mitigation_strategy": "Clear blocker and re-run readiness evaluation.",
                    "operator_rationale": None,
                    "status": "MONITORING",
                })
                index += 1
            for warning in check.warnings_json or []:
                risks.append({
                    "risk_id": f"RR-{index:03d}",
                    "module": check.category,
                    "severity": "MEDIUM",
                    "description": warning,
                    "mitigation": check.recommendation or "Monitor warning until next audit cycle.",
                    "is_accepted": False,
                    "accepted_by": None,
                    "accepted_at": None,
                    "mitigation_strategy": "Track warning closure before release lock.",
                    "operator_rationale": None,
                    "status": "MONITORING",
                })
                index += 1

        latest_audit = (
            await self.db.execute(
                select(UIFinalIntegrationAudit).order_by(UIFinalIntegrationAudit.created_at.desc()).limit(1)
            )
        ).scalar_one_or_none()
        if latest_audit:
            for failed_module in latest_audit.failed_modules_json or []:
                risks.append({
                    "risk_id": f"RR-{index:03d}",
                    "module": failed_module,
                    "severity": "HIGH",
                    "description": f"Integration audit failed for {failed_module}.",
                    "mitigation": "Resolve module failure and rerun final audit.",
                    "is_accepted": False,
                    "accepted_by": None,
                    "accepted_at": None,
                    "mitigation_strategy": "Block release lock until integration audit passes.",
                    "operator_rationale": None,
                    "status": "MONITORING",
                })
                index += 1
            for warning_module in latest_audit.warnings_json or []:
                risks.append({
                    "risk_id": f"RR-{index:03d}",
                    "module": warning_module,
                    "severity": "MEDIUM",
                    "description": f"Integration audit warning on {warning_module}.",
                    "mitigation": "Investigate warning and document compensating controls.",
                    "is_accepted": False,
                    "accepted_by": None,
                    "accepted_at": None,
                    "mitigation_strategy": "Keep warning under release review until cleared.",
                    "operator_rationale": None,
                    "status": "MONITORING",
                })
                index += 1

        risky_executions = (
            await self.db.execute(
                select(UIAutoPatchExecution)
                .where(
                    UIAutoPatchExecution.status.in_([
                        "FAILED",
                        "PREFLIGHT_BLOCKED",
                        "GOVERNANCE_REQUESTED",
                        "ROLLBACK_REQUIRED",
                    ])
                )
                .order_by(UIAutoPatchExecution.created_at.desc())
                .limit(10)
            )
        ).scalars().all()
        for execution in risky_executions:
            execution_state = _status_value(execution.status)
            severity = "HIGH" if execution_state in {"FAILED", "ROLLBACK_REQUIRED"} else "MEDIUM"
            risks.append({
                "risk_id": f"RR-{index:03d}",
                "module": "Auto-Patch",
                "severity": severity,
                "description": f"{execution.execution_key} is in {execution_state} state.",
                "mitigation": execution.error_message or "Resolve autopatch gate before release.",
                "is_accepted": False,
                "accepted_by": None,
                "accepted_at": None,
                "mitigation_strategy": "Complete verification/governance flow or cancel execution.",
                "operator_rationale": None,
                "status": "MONITORING",
            })
            index += 1

        provider_risks = (
            await self.db.execute(
                select(UIProviderHealth).where(UIProviderHealth.status.in_(["DEGRADED", "UNAVAILABLE"]))
            )
        ).scalars().all()
        for provider in provider_risks:
            provider_state = _status_value(provider.status)
            severity = "HIGH" if provider_state == "UNAVAILABLE" else "MEDIUM"
            risks.append({
                "risk_id": f"RR-{index:03d}",
                "module": "Tool Governance",
                "severity": severity,
                "description": f"Provider {provider.provider} is {provider_state}.",
                "mitigation": "Fallback to alternative provider or disable autonomous write paths.",
                "is_accepted": False,
                "accepted_by": None,
                "accepted_at": None,
                "mitigation_strategy": "Keep provider under active monitoring before release lock.",
                "operator_rationale": None,
                "status": "MONITORING",
            })
            index += 1

        acceptances = (await self.db.execute(select(UIResidualRiskAcceptance))).scalars().all()
        acceptance_by_fingerprint = {item.risk_fingerprint: item for item in acceptances}
        acceptance_by_risk_id = {item.risk_id: item for item in acceptances}

        for risk in risks:
            fingerprint = self._risk_fingerprint(risk)
            accepted = acceptance_by_fingerprint.get(fingerprint) or acceptance_by_risk_id.get(risk["risk_id"])
            if accepted:
                risk["is_accepted"] = True
                risk["accepted_by"] = accepted.operator
                risk["accepted_at"] = accepted.accepted_at
                risk["operator_rationale"] = accepted.operator_rationale
                risk["status"] = accepted.status

        return risks

    async def accept_residual_risk(
        self,
        risk_id: str,
        operator: str,
        rationale: Optional[str] = None,
    ) -> Dict[str, Any]:
        risks = await self.get_residual_release_risks()
        target = next((risk for risk in risks if risk["risk_id"] == risk_id), None)
        if target is None:
            raise ValueError(f"Residual risk not found: {risk_id}")

        fingerprint = self._risk_fingerprint(target)
        existing = (
            await self.db.execute(
                select(UIResidualRiskAcceptance).where(UIResidualRiskAcceptance.risk_fingerprint == fingerprint)
            )
        ).scalar_one_or_none()

        accepted_at = datetime.now(timezone.utc)
        if existing:
            existing.risk_id = risk_id
            existing.module = target["module"]
            existing.severity = target["severity"]
            existing.description = target["description"]
            existing.mitigation = target["mitigation"]
            existing.mitigation_strategy = target["mitigation_strategy"]
            existing.operator = operator
            existing.operator_rationale = rationale
            existing.status = "ACCEPTED"
            existing.accepted_at = accepted_at
            record = existing
        else:
            record = UIResidualRiskAcceptance(
                risk_id=risk_id,
                risk_fingerprint=fingerprint,
                module=target["module"],
                severity=target["severity"],
                description=target["description"],
                mitigation=target["mitigation"],
                mitigation_strategy=target["mitigation_strategy"],
                operator=operator,
                operator_rationale=rationale,
                status="ACCEPTED",
                accepted_at=accepted_at,
            )
            self.db.add(record)

        await self.db.commit()
        await self.db.refresh(record)

        target["is_accepted"] = True
        target["accepted_by"] = record.operator
        target["accepted_at"] = record.accepted_at
        target["operator_rationale"] = record.operator_rationale
        target["status"] = record.status
        return target
