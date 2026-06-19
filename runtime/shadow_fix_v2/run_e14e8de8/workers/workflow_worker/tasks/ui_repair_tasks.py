import asyncio
from .celery_app import celery_app, logger
from services.ui_repair.monitoring_scheduler import MonitoringScheduler

@celery_app.task(name="workers.workflow_worker.tasks.ui_repair_tasks.ui_smoke_monitor_task")
def ui_smoke_monitor_task():
    """
    Celery task that runs the UI smoke monitoring cycle.
    """
    logger.info("Starting peridic UI smoke monitoring task...")
    
    # Run async function in sync Celery worker
    loop = asyncio.get_event_loop()
    if loop.is_running():
        # This shouldn't happen in a standard Celery worker, but safety first
        result = asyncio.run_coroutine_threadsafe(
            MonitoringScheduler.run_scheduled_monitoring(), 
            loop
        ).result()
    else:
        result = asyncio.run(MonitoringScheduler.run_scheduled_monitoring())
    
    logger.info(f"UI smoke monitoring task finished: {result.get('status')}")
    return result
