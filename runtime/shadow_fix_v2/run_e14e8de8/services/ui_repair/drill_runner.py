import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, cast
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.ui_repair_models import (
    UIAdvancedChaosScenario, UIAdvancedChaosRun, FailureType, UIRepairSeverity
)
from .playwright_runner import UIEvidenceRunner
from .advanced_failure_injector import AdvancedFailureInjector
from .operator_escalation_service import OperatorEscalationService

class AdvancedDrillRunner:
    """Executes advanced chaos drills using failure injection and monitoring validation."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.runner = UIEvidenceRunner()

    async def run_advanced_drill(self, scenario_id: UUID, triggered_by: str) -> Dict[str, Any]:
        # 1. Fetch Scenario
        stmt = select(UIAdvancedChaosScenario).where(UIAdvancedChaosScenario.id == scenario_id)
        scenario = (await self.db.execute(stmt)).scalar_one_or_none()
        if not scenario:
            return {"status": "error", "message": "Scenario not found"}

        # 2. Create Run Record
        scenario_any = cast(Any, scenario)
        run = UIAdvancedChaosRun(
            scenario_id=scenario_any.id,
            chaos_type=scenario_any.chaos_type,
            target_route=scenario_any.target_route,
            status="RUNNING",
            started_at=datetime.now(timezone.utc)
        )
        self.db.add(run)
        await self.db.commit()
        await self.db.refresh(run)

        try:
            # 3. Setup Injection and Monitor
            # We use UIEvidenceRunner to get a page, then wrap it with AdvancedFailureInjector
            async with self.runner._get_context() as (browser, context):
                page = await context.new_page()
                injector = AdvancedFailureInjector(context, page)
                
                # Configure injection based on scenario
                scenario_any = cast(Any, scenario)
                config = self._get_injection_config(scenario)
                await injector.inject(str(scenario_any.chaos_type), config)
                
                # 4. Navigate and Capture (Validation)
                await page.goto(str(scenario_any.target_route), wait_until="networkidle")
                await asyncio.sleep(2) # Wait for potential failures to trigger
                
                # Collect evidence
                results = await self.runner._analyze_page(page, str(scenario_any.target_route))
                
                # 5. Determine Result
                detected = self._verify_detection(scenario, results)
                run_any = cast(Any, run)
                run_any.detected_by_monitoring = detected
                run_any.detected_failure_type = results.get("failure_type")
                run_any.detected_severity = results.get("severity")
                run_any.passed = detected
                
                # 6. Cleanup
                await injector.cleanup()
                run_any.cleanup_status = "SUCCESS"

            run_any = cast(Any, run)
            run_any.status = "COMPLETED"
            run_any.finished_at = datetime.now(timezone.utc)
            run_any.duration_seconds = int((run_any.finished_at - run_any.started_at).total_seconds())
            
            # 7. Escalation if needed
            if run.detected_severity in ["CRITICAL", "URGENT"]:
                # Trigger escalation (need sync session helper or adapt service)
                # For brevity, we'll assume a helper handles this
                pass

        except Exception as e:
            run_any = cast(Any, run)
            run_any.status = "FAILED"
            run_any.failure_reason = str(e)
            run_any.cleanup_status = "FAILED"
        
        await self.db.commit()
        run_any = cast(Any, run)
        return {"status": run_any.status, "run_id": str(run_any.id), "passed": run_any.passed}

    def _get_injection_config(self, scenario: UIAdvancedChaosScenario) -> Dict[str, Any]:
        config: Dict[str, Any] = {
            "target_api": str(scenario.target_api) if scenario.target_api else "**/*",
            "pattern": str(scenario.target_resource) if scenario.target_resource else None
        }
        if str(scenario.chaos_type) == "NETWORK_LATENCY":
            config["latency_ms"] = 3000
        elif str(scenario.chaos_type) == "JS_CHUNK_BLOCK":
            config["pattern"] = "**/*.js"
        return config

    def _verify_detection(self, scenario: UIAdvancedChaosScenario, results: Dict[str, Any]) -> bool:
        # Pass if monitoring detected the expected failure type or visual degradation
        if scenario.expected_detection and results.get("failure_type") == scenario.expected_detection:
            return True
        if results.get("status") == "FAIL":
            return True
        return False
