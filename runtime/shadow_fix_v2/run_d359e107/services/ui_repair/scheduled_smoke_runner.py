import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, cast
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from libs.db.models.ui_repair_models import UIMonitoringConfig, UIMonitoringRun, UIRepairCase, UIRepairStatus
from libs.infra.router_registry import router_registry
from .service import UIRepairService
from .route_health_service import RouteHealthService
from .self_healing_policy import SelfHealingPolicy
from .recurrence_detector import RecurrenceDetector
from .notification_adapter import NotificationAdapter
from services.observability.logging import get_logger

_log = get_logger("ui_monitoring_runner")

class ScheduledSmokeRunner:
    """
    Phase 6: Scheduled Smoke Runner.
    Orchestrates the background monitoring loop.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repair_service = UIRepairService(db)
        self.health_service = RouteHealthService(db)
        self.notifier = NotificationAdapter(db)


    async def run_monitoring_cycle(self, triggered_by: str = "SCHEDULED") -> Dict[str, Any]:
        """
        Executes a single monitoring cycle.
        """
        # 1. Fetch Config
        stmt_cfg = select(UIMonitoringConfig).limit(1)
        config_obj = (await self.db.execute(stmt_cfg)).scalar_one_or_none()
        if not config_obj or not config_obj.enabled:
            _log.info("UI Monitoring is disabled or not configured.")
            return {"status": "skipped", "reason": "disabled"}

        config = {
            "auto_repair_enabled": config_obj.auto_repair_enabled,
            "auto_repair_risk_threshold": config_obj.auto_repair_risk_threshold,
            "max_repairs_per_hour": config_obj.max_repairs_per_hour,
            "max_repairs_per_day": config_obj.max_repairs_per_day,
            "route_scope_json": config_obj.route_scope_json
        }

        # 2. Create Run Record
        run = UIMonitoringRun(status="RUNNING", triggered_by=triggered_by)
        self.db.add(run)
        cast(Any, run).status = "RUNNING"
        await self.db.commit()
        await self.db.refresh(run)

        _log.info(f"UI Monitoring: Starting run {cast(Any, run).id}")

        # 3. Determine Route Scope
        all_routes = [r["path"] for r in router_registry.get_all_routes()]
        from .monitoring_policy import MonitoringPolicy
        scope = MonitoringPolicy.get_scoped_routes(config, all_routes)
        
        # 4. Execute Smoke Tests (Reuse existing runner)
        # Note: In a real world, this might take minutes. 
        # For the demo, we assume the runner is async and non-blocking.
        smoke_results = await self.repair_service.runner.run_smoke_test(scope)
        
        passed = 0
        failed = 0
        degraded = 0
        auto_repairs = 0
        cases_created = 0
        cases_updated = 0

        # 5. Process Results
        for res in smoke_results:
            status = res.get("status", "FAIL")
            route = res.get("route")
            
            # Record Health History
            await self.health_service.record_snapshot(
                route=str(route),
                status=str(status),
                http_status=int(res.get("http_status", 0)),
                response_time=float(res.get("response_time_ms", 0)),
                run_id=cast(Any, run).id
            )

            if status == "PASS":
                passed += 1
            else:
                failed += 1
                # 6. Handle Failure & Deduplication
                # We reuse the repair_service._handle_failure which creates/updates cases
                is_new = await self.repair_service._handle_failure(res)
                if is_new:
                    cases_created += 1
                else:
                    cases_updated += 1
                
                # 7. Self-Healing Evaluation
                stmt_case = select(UIRepairCase).where(UIRepairCase.route == route, UIRepairCase.status != "RESOLVED").order_by(UIRepairCase.created_at.desc()).limit(1)
                case_obj = (await self.db.execute(stmt_case)).scalar_one_or_none()
                
                if case_obj:
                    case = cast(Any, case_obj)
                    
                    # Fetch health history for recurrence detection
                    history = await self.health_service.get_route_history(str(route), limit=10)
                    
                    is_flapping = RecurrenceDetector.detect_flapping(history)
                    is_chronic = RecurrenceDetector.is_chronic_failure(history)
                    
                    if is_flapping:
                        _log.warning(f"UI Monitoring: Flapping route detected: {route}")
                        # Could trigger specialized diagnostic or notification
                    
                    # Fetch actual stats for policy evaluation
                    stats = await self.repair_service.get_repair_stats()
                    
                    should_auto, reason = SelfHealingPolicy.evaluate_auto_repair(config, {"severity": case.severity}, stats)
                    
                    if should_auto:
                        _log.info(f"Self-Healing: Triggering auto-repair for case {case.id} (Reason: {reason})")
                        # Background task to avoid blocking the cycle
                        asyncio.create_task(self.repair_service.trigger_autonomous_repair(str(case.id)))
                        auto_repairs += 1
                        if config_obj.notify_on_repair_started:
                            await self.notifier.send_alert(f"Auto-repair started for {route}")
                    else:
                        _log.info(f"Self-Healing: Skipping auto-repair for {route}. Reason: {reason}")
                        if config_obj.notify_on_failure:
                            await self.notifier.send_alert(f"UI Failure detected on {route}. Manual review required.")

        # 8. Finalize Run
        cast(Any, run).status = "COMPLETED"
        cast(Any, run).finished_at = datetime.now()
        cast(Any, run).total_routes = len(smoke_results)
        cast(Any, run).passed_routes = passed
        cast(Any, run).failed_routes = failed
        cast(Any, run).degraded_routes = degraded
        cast(Any, run).auto_repair_started_count = auto_repairs
        cast(Any, run).cases_created_count = cases_created
        cast(Any, run).cases_updated_count = cases_updated
        cast(Any, run).summary_json = {"results": smoke_results}
        
        await self.db.commit()
        _log.info(f"UI Monitoring: Run {run.id} finished. Passed: {passed}, Failed: {failed}, Auto-Repairs: {auto_repairs}")
        
        return {
            "run_id": str(run.id),
            "passed": passed,
            "failed": failed,
            "auto_repairs": auto_repairs
        }
