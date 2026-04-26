"""
libs/infra/router_registry.py — Phase 13.04
Centralized router registration for Sovereign AGI services.
"""
from fastapi import FastAPI
from services.workflow_api.router import router as workflow_router
from services.auth.router import router as auth_router
from services.workflow_api.metrics_router import router as metrics_router
from services.observability.mesh_status_api import router as mesh_router
from services.observability.fleet_status_api import router as fleet_router
from services.governance.mesh_actions_api import router as mesh_actions_router
from services.improve.router import router as repair_lab_router

def register_routers(app: FastAPI):
    """
    Registers all service routers to the main FastAPI application.
    All API endpoints are prefixed with /api/v1 to avoid conflicts with
    static dashboard files served at the root.
    """
    from fastapi import APIRouter
    api_v1 = APIRouter(prefix="/api/v1")

    # 1. Auth Service (mapped to /api/v1/auth)
    api_v1.include_router(auth_router, prefix="/auth", tags=["Auth"])

    # 2. Workflow API (Now correctly mapped to /api/v1/workflows)
    api_v1.include_router(workflow_router)

    # 3. Phase 17 Metrics API (Now mapped to /api/v1/metrics/phase17)
    api_v1.include_router(metrics_router)

    # 4. Governance & Self-Healing (Now mapped to /api/v1/...)
    # This includes critical endpoints like /approvals, /incidents, /improvements
    from services.workflow_api.governance_router import router as governance_router
    api_v1.include_router(governance_router)

    # 5. Observability & Fleet Status
    api_v1.include_router(mesh_router)
    api_v1.include_router(fleet_router) # Fleet router prefix handling
    api_v1.include_router(mesh_actions_router)

    # 6. Repair Lab & Self-Tuning
    api_v1.include_router(repair_lab_router)

    # 7. Phase 31: Autonomous Learning
    from services.governance.learning_api import router as learning_router
    api_v1.include_router(learning_router)

    # Register the unified API router
    app.include_router(api_v1)
