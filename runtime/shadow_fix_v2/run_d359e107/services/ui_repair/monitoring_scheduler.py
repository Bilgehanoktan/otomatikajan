from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.session import AsyncSessionLocal
from .scheduled_smoke_runner import ScheduledSmokeRunner
from services.observability.logging import get_logger

_log = get_logger("ui_monitoring_scheduler")

class MonitoringScheduler:
    """
    Phase 6: Monitoring Scheduler.
    Bridges the Celery periodic tasks to the ScheduledSmokeRunner.
    """

    @staticmethod
    async def run_scheduled_monitoring():
        """
        Entry point for the periodic Celery task.
        Runs a full monitoring cycle.
        """
        _log.info("UI Monitoring Scheduler: Initiating scheduled smoke run.")
        async with AsyncSessionLocal() as db:
            runner = ScheduledSmokeRunner(db)
            try:
                result = await runner.run_monitoring_cycle(triggered_by="SCHEDULED")
                _log.info(f"UI Monitoring Scheduler: Cycle finished. Run ID: {result.get('run_id')}")
                return result
            except Exception as e:
                _log.error(f"UI Monitoring Scheduler failed: {e}")
                return {"status": "error", "message": str(e)}

    @staticmethod
    async def run_manual_monitoring():
        """
        Entry point for manual monitoring triggers.
        """
        _log.info("UI Monitoring Scheduler: Initiating manual smoke run.")
        async with AsyncSessionLocal() as db:
            runner = ScheduledSmokeRunner(db)
            return await runner.run_monitoring_cycle(triggered_by="MANUAL")
