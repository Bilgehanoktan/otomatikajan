import os
import logging

import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from libs.config import ALLOWED_HEADERS, ALLOWED_METHODS, ALLOWED_ORIGINS
from services.workflow_api.router import router as workflow_router
from services.workflow_api.governance_router import router as governance_router
from services.workflow_api.repair_lab_router import router as repair_lab_router
from services.workflow_api.metrics_router import router as metrics_router
from services.workflow_api.health_router import router as health_router, websocket_endpoint

from services.workflow_api.compatibility_router import router as compatibility_router
from services.auth.router import router as auth_router
from services.observability.fleet_status_api import router as fleet_status_router
from services.workflow_api.fleet_router import router as fleet_ops_router
from services.observability.mesh_status_api import router as mesh_status_router
from services.governance.mesh_actions_api import router as mesh_actions_router
from services.workflow_api.governor_router import router as governor_api_router
from services.governance.harness_api import router as harness_router
from libs.db.session import init_db
from services.orchestration.application.job_queue import job_queue
from services.orchestration.application.sovereign_cortex import sovereign_cortex

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Sovereign AGI Workflow API",
    description="Mission Control Plane for Autonomous Governance & Repair",
    version="12.1.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=ALLOWED_METHODS,
    allow_headers=ALLOWED_HEADERS,
)

# Include Routers
app.include_router(workflow_router, prefix="/api/v1/workflows")
app.include_router(governance_router, prefix="/api/v1/governance")
app.include_router(repair_lab_router, prefix="/api/v1/repair-lab")
app.include_router(metrics_router, prefix="/api/v1/metrics")
app.include_router(health_router, prefix="/api/v1/health")
app.include_router(compatibility_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1/auth")
app.include_router(fleet_status_router, prefix="/api/v1/fleet")
app.include_router(fleet_ops_router, prefix="/api/v1/fleet/ops")
app.include_router(mesh_status_router, prefix="/api/v1/mesh")
app.include_router(mesh_actions_router, prefix="/api/v1/mesh/actions")
app.include_router(governor_api_router, prefix="/api/v1/governance/governor")
app.include_router(harness_router, prefix="/api/v1/harness")


@app.websocket("/ws/events")
async def websocket_route(websocket: WebSocket):
    await websocket_endpoint(websocket)

@app.on_event("startup")
async def startup_event():
    await init_db()
    print("Database Initialized.")

    try:
        from libs.db.session import is_db_degraded
        from services.workflow_api.runtime_diagnostics import RuntimeDiagnosticsService

        queue_stats = job_queue.stats() if hasattr(job_queue, "stats") else {}
        startup_findings = RuntimeDiagnosticsService(
            queue_stats=queue_stats,
            db_is_fallback=is_db_degraded(),
        ).collect()
        for finding in startup_findings:
            if finding.id == "profile_mismatch":
                logger.error(
                    "RUNTIME_CONFIG_ACTION id=profile_mismatch fix=\"set RUNTIME_PROFILE=full-stack-local LOCAL_DEV_DB_STRATEGY=primary QUEUE_BACKEND=celery REDIS_ENABLED=true CELERY_ENABLED=true then restart\" evidence=%s",
                    finding.evidence,
                )
            elif finding.severity in {"error", "warning"}:
                logger.warning("RUNTIME_DIAGNOSTIC id=%s action=%s", finding.id, finding.recommended_action)
    except Exception as exc:
        logger.warning("Runtime startup diagnostics failed: %s", exc)
    
    # Register core handlers
    from libs.workflow.runner import register_workflow_handlers
    await register_workflow_handlers(job_queue)
    print("Job handlers registered via WorkflowRunner.")
    
    # Start the worker loop
    await job_queue.start(num_workers=2)
    print("Job Queue Worker loop started.")

    # Proactive Infrastructure Audit
    try:
        from libs.diagnostics.auditor import InfrastructureAuditor
        import asyncio
        asyncio.create_task(InfrastructureAuditor.run_and_report())
        print("Proactive Infrastructure Auditor initiated.")
    except Exception as e:
        print(f"Failed to start Auditor: {e}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "workflow_api"}

if __name__ == "__main__":
    uvicorn.run(
        "services.workflow_api.main:app",
        host=os.getenv("WORKFLOW_API_HOST", "127.0.0.1"),
        port=int(os.getenv("WORKFLOW_API_PORT", "8000")),
        reload=True,
    )
