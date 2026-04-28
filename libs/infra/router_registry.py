"""
libs/infra/router_registry.py — Phase 13.04
Centralized router registration for Sovereign AGI services.
"""
from fastapi import FastAPI
from services.workflow_api.router import router as workflow_router
from services.auth.router import router as auth_router
from services.workflow_api.metrics_router import router as metrics_router
from services.workflow_api.health_router import router as health_router
from services.workflow_api.bridge_router import router as bridge_router
from services.observability.mesh_status_api import router as mesh_router
from services.observability.fleet_status_api import router as fleet_router
from services.governance.mesh_actions_api import router as mesh_actions_router
from services.improve.router import router as repair_lab_router
from services.workflow_api.fleet_router import router as fleet_orchestra_router

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

    # 4. Governance & Self-Healing
    # Keep direct mounts for legacy/simple-rest resources like /api/v1/approvals,
    # and also provide the explicit /api/v1/governance/* namespace expected by
    # several newer control-plane screens.
    from services.workflow_api.governance_router import router as governance_router
    api_v1.include_router(governance_router)
    api_v1.include_router(governance_router, prefix="/governance")

    # 5. Health & bridge aliases used by the modern control plane
    api_v1.include_router(health_router)
    api_v1.include_router(bridge_router)

    # 6. Observability & Fleet Status
    api_v1.include_router(mesh_router)
    api_v1.include_router(fleet_router) # Fleet router prefix handling
    api_v1.include_router(fleet_orchestra_router) # Phase 12 Orchestra
    api_v1.include_router(mesh_actions_router)

    # 7. Repair Lab & Self-Tuning
    api_v1.include_router(repair_lab_router)
    # Alias for frontend compatibility
    api_v1.include_router(repair_lab_router, prefix="/repair-lab")

    # 8. Phase 31: Autonomous Learning
    from services.governance.learning_api import router as learning_router
    from services.workflow_api.governor_router import router as governor_router
    api_v1.include_router(learning_router)
    api_v1.include_router(governor_router, prefix="/governance")

    # Register the unified API router
    app.include_router(api_v1)
