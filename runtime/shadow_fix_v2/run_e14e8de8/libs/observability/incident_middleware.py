"""
libs/observability/incident_middleware.py - Phase 16
Middleware that captures unhandled exceptions and 5xx errors as OperationalIncidents,
triggering the autonomous self-correction loop.
"""
import traceback
import uuid
import logging
import asyncio
from pathlib import Path
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from libs.config import APP_ENV, QUEUE_BACKEND, REDIS_URL
from libs.db.session import AsyncSessionLocal

logger = logging.getLogger("sovereign.incident_middleware")


def _queue_backend_name() -> str:
    return (QUEUE_BACKEND or "auto").lower()


def _should_dispatch_auto_fix() -> bool:
    backend = _queue_backend_name()

    # Local/dev ortamda in-process queue ile self-healing aktif kalmali.
    if APP_ENV == "development" and backend in {"inprocess", "local", "memory"}:
        return True
    if APP_ENV == "development" and backend != "celery":
        return False

    if backend == "celery" and not REDIS_URL:
        return False
    return True


class SovereignIncidentMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        try:
            response = await call_next(request)

            if response.status_code >= 500:
                try:
                    await self._capture_incident(request, f"HTTP {response.status_code}")
                except Exception as cap_e:
                    logger.error(f"Failed to capture 5xx incident: {cap_e}")

            return response

        except Exception as e:
            # Capture total failure - carefully to avoid recursion
            try:
                await self._capture_incident(request, str(e), traceback.format_exc())
            except Exception as cap_e:
                logger.error(f"Failed to capture exception incident: {cap_e}")
            
            # Re-raise to let standard exception handlers handle it
            raise e from None

    async def _capture_incident(self, request: Request, message: str, stack_trace: str = None):
        """Creates an OperationalIncident and triggers auto-fix."""
        try:
            project_id = request.headers.get("X-Project-ID")
            try:
                if project_id:
                    project_id = uuid.UUID(project_id)
            except ValueError:
                project_id = None

            async with AsyncSessionLocal() as db:
                from libs.db.repositories.repository import OperationalIncidentRepository
                
                payload = {
                    "path": request.url.path,
                    "method": request.method,
                    "query_params": str(request.query_params),
                    "stack_trace": stack_trace,
                }

                incident = await OperationalIncidentRepository.create(
                    db,
                    incident_type="api_exception",
                    message=message,
                    severity="high",
                    project_id=project_id,
                    payload=payload,
                )
                await db.commit()

                logger.warning("Incident %s captured by middleware. Triggering auto-fix...", incident.id)

                if not _should_dispatch_auto_fix():
                    logger.info(
                        "Local degraded mode active; Celery auto-fix dispatch skipped for incident %s.",
                        incident.id,
                    )
                    return

                backend = _queue_backend_name()
                try:
                    if backend == "celery":
                        from workers.workflow_worker.tasks.project_tasks import auto_fix_incident_task
                        auto_fix_incident_task.apply_async(
                            args=[str(incident.id)],
                            queue="critical",
                        )
                    else:
                        await self._dispatch_inline_auto_fix(str(incident.id))
                except Exception as task_e:
                    logger.error(f"Failed to dispatch auto-fix task for incident {incident.id}: {task_e}")

        except Exception as inner_e:
            logger.error(f"Failed to capture incident in middleware: {inner_e}")

    async def _dispatch_inline_auto_fix(self, incident_id: str):
        """
        Celery disindaki local-dev modlarda incident auto-fix'i event loop
        icinde arka planda calistirir.
        """
        try:
            from services.improve.self_correction_service import SelfCorrectionService
            from services.orchestration.agi.cognitive.sovereign_cortex import sovereign_cortex as orchestrator

            project_root = str(Path(__file__).resolve().parents[2])
            service = SelfCorrectionService(
                model_orch=orchestrator.model_orch,
                project_root=project_root,
            )

            asyncio.create_task(service.process_incident(incident_id))
            logger.info(
                "In-process auto-fix dispatched for incident %s (backend=%s).",
                incident_id,
                _queue_backend_name(),
            )
        except Exception as exc:
            logger.error("Failed to dispatch in-process auto-fix for %s: %s", incident_id, exc)
