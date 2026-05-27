import logging
import os
import sys
import asyncio

import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from libs.config import ALLOWED_HEADERS, ALLOWED_METHODS, ALLOWED_ORIGINS
from libs.db.session import init_db
from services.auth.router import router as auth_router
from services.governance.harness_api import router as harness_router
from services.governance.learning_api import router as learning_router
from services.governance.mesh_actions_api import router as mesh_actions_router
from services.observability.fleet_status_api import router as fleet_status_router
from services.observability.mesh_status_api import router as mesh_status_router
from services.orchestration.application.job_queue import job_queue
from services.ui_repair.router import router as ui_repair_router
from services.workflow_api.compatibility_router import router as compatibility_router
from services.workflow_api.fleet_router import router as fleet_ops_router
from services.workflow_api.governance_router import router as governance_router
from services.workflow_api.governor_router import router as governor_api_router
from services.workflow_api.health_router import router as health_router
from services.workflow_api.health_router import websocket_endpoint
from services.workflow_api.metrics_router import router as metrics_router
from services.workflow_api.repair_lab_router import router as repair_lab_router
from services.workflow_api.router import router as workflow_router
from services.orchestration.ceo.router import router as ceo_engine_router
from services.workflow_api.ceo_router import router as ceo_bridge_router
from services.workflow_api.project_factory_router import router as project_factory_router
from services.workflow_api.mcp_router import router as mcp_router
from services.workflow_api.debate_router import router as debate_router

from contextlib import asynccontextmanager

if sys.platform == "win32" and hasattr(asyncio, "WindowsProactorEventLoopPolicy"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
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
        import asyncio

        from libs.diagnostics.auditor import InfrastructureAuditor
        asyncio.create_task(InfrastructureAuditor.run_and_report())
        print("Proactive Infrastructure Auditor initiated.")
    except Exception as e:
        print(f"Failed to start Auditor: {e}")

    yield

    # Shutdown actions
    try:
        await job_queue.stop()
        print("Job Queue Worker loop stopped.")
    except Exception as e:
        print(f"Failed to stop Job Queue Workers: {e}")

    try:
        import libs.db.session as db_session
        if db_session._engine is not None:
            await db_session._engine.dispose()
            db_session._engine = None
        print("Database engine disposed cleanly.")
    except Exception as e:
        print(f"Failed to dispose database engine: {e}")

app = FastAPI(
    title="Sovereign AGI Workflow API",
    description="Mission Control Plane for Autonomous Governance & Repair",
    version="12.1.0",
    lifespan=lifespan
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
app.include_router(learning_router, prefix="/api/v1")
app.include_router(ui_repair_router, prefix="/api/v1/ui-repair")
app.include_router(ceo_engine_router, prefix="/api/v1/ceo")
app.include_router(ceo_bridge_router, prefix="/api/v1/ceo")
app.include_router(project_factory_router, prefix="/api/v1/project-factory")
app.include_router(mcp_router, prefix="/api/v1/mcp")
app.include_router(debate_router, prefix="/api/v1/debate")

@app.websocket("/ws/events")
async def websocket_route(websocket: WebSocket):
    await websocket_endpoint(websocket)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "workflow_api"}

if __name__ == "__main__":
    uvicorn.run(
        "services.workflow_api.main:app",
        host=os.getenv("WORKFLOW_API_HOST", "127.0.0.1"),
        port=int(os.getenv("WORKFLOW_API_PORT", "8000")),
        reload=os.getenv("WORKFLOW_API_RELOAD", "false").strip().lower() in {"1", "true", "yes", "on"},
    )
