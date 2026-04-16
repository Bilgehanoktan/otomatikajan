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

def register_routers(app: FastAPI):
    """
    Registers all service routers to the main FastAPI application.
    """
    # Auth Service (mapped to /api/v1/auth)
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
    
    # Workflow API (contains /api/v1 prefix in its own definition)
    app.include_router(workflow_router)
    
    # Phase 17 Metrics API
    app.include_router(metrics_router)
    
    # Observability & Actions
    app.include_router(mesh_router)
    app.include_router(fleet_router, prefix="/api/v1")
    app.include_router(mesh_actions_router)
