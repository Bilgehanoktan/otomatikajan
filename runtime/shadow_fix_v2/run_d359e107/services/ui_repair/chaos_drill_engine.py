import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, cast
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from libs.db.models.ui_repair_models import (
    UIChaosDrillScenario, UIChaosDrillRun, UIRepairCase, UIMonitoringRun
)
from .failure_injector import FailureInjector
from .scheduled_smoke_runner import ScheduledSmokeRunner
from .repair_evidence_writer import UIRepairEvidenceWriter
from services.observability.logging import get_logger

_log = get_logger("ui_chaos_drill_engine")

class ChaosDrillEngine:
    """
    Phase 8: Chaos Drill Engine.
    Orchestrates the execution of resilience drills.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.smoke_runner = ScheduledSmokeRunner(db)
        self.evidence_writer = UIRepairEvidenceWriter(db)

    async def run_drill(self, scenario_id: UUID, triggered_by: str = "MANUAL") -> Dict[str, Any]:
        """
        Executes a specific chaos drill scenario.
        """
        # 1. Fetch Scenario
        scenario = await self.db.get(UIChaosDrillScenario, scenario_id)
        if not scenario:
            return {"status": "error", "message": "Scenario not found"}

        # 2. Safety Check
        # In a real system, we'd check environment variables (e.g., SOVEREIGN_ENV != 'prod')
        if scenario.is_destructive and not scenario.requires_sandbox:
             _log.warning(f"Chaos Drill: Destructive drill {scenario.name} requested outside sandbox. Blocking.")
             return {"status": "blocked", "reason": "SAFETY_VIOLATION"}

        # 3. Initialize Run Record
        run = UIChaosDrillRun(
            scenario_id=scenario_id,
            status="RUNNING",
            triggered_by=triggered_by,
            target_route=scenario.target_route,
            injected_failure_type=scenario.failure_type,
            environment="sandbox" # Mocked for now
        )
        self.db.add(run)
        await self.db.commit()
        await self.db.refresh(run)

        injection_id = None
        try:
            # 4. Inject Failure
            injection_id = FailureInjector.inject_failure(scenario)

            # 5. Trigger Monitoring Cycle
            # We trigger a manual cycle to catch the injected failure immediately
            monitor_result = await self.smoke_runner.run_monitoring_cycle(triggered_by=f"DRILL_{run.id}")
            
            # 6. Analyze Detection
            monitoring_run_id = UUID(monitor_result["run_id"])
            run.monitoring_run_id = monitoring_run_id
            
            # Fetch the monitoring result for the target route
            # We'd ideally check if a case was created for this route
            stmt_case = select(UIRepairCase).where(
                UIRepairCase.route == scenario.target_route,
                UIRepairCase.created_at >= run.started_at
            ).order_by(UIRepairCase.created_at.desc()).limit(1)
            
            case_obj = (await self.db.execute(stmt_case)).scalar_one_or_none()
            
            if case_obj:
                run.detection_status = "DETECTED"
                run.repair_case_id = case_obj.id
                run.detected_failure_type = case_obj.failure_type
                run.detected_severity = case_obj.severity
                
                # Check Policy and Repair (Mocked check for now)
                # In real flow, ScheduledSmokeRunner would have already triggered it
                # We just verify if it matches expectations
                run.passed = (
                    run.detected_failure_type == scenario.expected_detection and
                    run.detected_severity == scenario.expected_severity
                )
            else:
                run.detection_status = "MISSED"
                run.passed = False
                run.failure_reason = "Failure not detected by monitoring loop."

        except Exception as e:
            _log.error(f"Chaos Drill {run.id} failed: {e}")
            run.status = "FAILED"
            run.failure_reason = str(e)
            run.passed = False
        finally:
            # 7. Cleanup
            if injection_id:
                FailureInjector.cleanup_injection(injection_id)
            
            run.finished_at = datetime.now()
            if run.status == "RUNNING":
                run.status = "PASSED" if run.passed else "FAILED"
            
            await self.db.commit()
            
            # 8. Evidence Linkage
            await self.evidence_writer.log_event(
                case_id=run.repair_case_id or UUID(int=0), # Dummy if missed
                attempt_id=None,
                event_type="UI_CHAOS_DRILL_COMPLETED",
                status=run.status,
                payload={
                    "drill_id": str(run.id),
                    "scenario": scenario.name,
                    "passed": run.passed,
                    "detection": run.detection_status
                }
            )

        return {
            "run_id": str(run.id),
            "passed": run.passed,
            "status": run.status,
            "detection": run.detection_status
        }
