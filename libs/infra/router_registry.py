"""
libs/infra/router_registry.py — Phase 13.04
Centralized router registration for Sovereign AGI services.
"""
from fastapi import FastAPI
from services.workflow_api.router import router as workflow_router
from services.auth.router import router as auth_router

def register_routers(app: FastAPI):
    """
    Registers all service routers to the main FastAPI application.
    """
    # Auth Service (mapped to /api/v1/auth)
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
    
    # Workflow API (contains /api/v1 prefix in its own definition)
    app.include_router(workflow_router)
    
    # Add other routers here as services are migrated
