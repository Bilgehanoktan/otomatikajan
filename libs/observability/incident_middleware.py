"""
libs/observability/incident_middleware.py - Phase 16
Middleware that captures unhandled exceptions and 5xx errors as OperationalIncidents,
triggering the autonomous self-correction loop.
"""
import traceback
import uuid
import logging
from datetime import datetime, timezone
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from libs.db.session import AsyncSessionLocal
from libs.db.repositories.repository import OperationalIncidentRepository
from workers.workflow_worker.tasks.project_tasks import auto_fix_incident_task

logger = logging.getLogger("sovereign.incident_middleware")

class SovereignIncidentMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        try:
            response = await call_next(request)
            
            if response.status_code >= 500:
                await self._capture_incident(request, f"HTTP {response.status_code}")
                
            return response
            
        except Exception as e:
            # Capture total failure
            await self._capture_incident(request, str(e), traceback.format_exc())
            # Re-raise to let standard exception handlers handle it
            raise e from None

    async def _capture_incident(self, request: Request, message: str, stack_trace: str = None):
        """Creates an OperationalIncident and triggers auto-fix."""
        try:
            # Try to identify project_id from headers or query (if applicable)
            project_id = request.headers.get("X-Project-ID")
            try:
                if project_id:
                    project_id = uuid.UUID(project_id)
            except ValueError:
                project_id = None

            async with AsyncSessionLocal() as db:
                payload = {
                    "path": request.url.path,
                    "method": request.method,
                    "query_params": str(request.query_params),
                    "stack_trace": stack_trace
                }
                
                incident = await OperationalIncidentRepository.create(
                    db,
                    incident_type="api_exception",
                    message=message,
                    severity="high",
                    project_id=project_id,
                    payload=payload
                )
                await db.commit()
                
                logger.warning(f"🚨 Incident {incident.id} captured by middleware. Triggering auto-fix...")
                
                # Trigger Autonomous Self-Correction Loop
                auto_fix_incident_task.apply_async(
                    args=[str(incident.id)],
                    queue="critical"
                )
                
        except Exception as inner_e:
            logger.error(f"Failed to capture incident in middleware: {inner_e}")
