"""
Sovereign AGI — Phase 22
workers/workflow_worker/tasks/mesh_tasks.py
Dedicated tasks for mesh health monitoring and regional pulsing.
"""
from workers.workflow_worker.tasks.celery_app import celery_app
from workers.workflow_worker.tasks.project_tasks import run_async
from services.observability.logging import get_logger

logger = get_logger("workers.mesh")

@celery_app.task(name="workers.workflow_worker.tasks.mesh_tasks.mesh_pulse_task")
def mesh_pulse_task():
    """Mesh ağındaki bölgelerin sağlık ve gecikme verilerini tazeler (Heartbeat)."""
    async def _execute():
        from services.orchestration.latency_adapter import latency_adapter
        regions = ["us-east-1", "eu-central-1", "ap-southeast-1"]
        for r in regions:
            try:
                # Update health and latency observations
                await latency_adapter.get_health_score(r)
                await latency_adapter.get_latency("us-east-1", r)
            except Exception as e:
                logger.error(f"Error pulsing region {r}: {e}")
        return True

    return run_async(_execute())
