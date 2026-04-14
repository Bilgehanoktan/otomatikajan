"""
services/workflow_api/main.py — Phase 13.04
Primary entry point for the Sovereign AGI Workflow Control Plane.
"""
from __future__ import annotations

import os
from fastapi import FastAPI
import uvicorn

from libs.infra.lifespan import lifespan
from libs.infra.middleware import configure_middleware
from services.workflow_api.router import router as workflow_router
from services.observability.logging import get_logger

logger = get_logger("workflow_api")

def create_app() -> FastAPI:
    """Scaffold the FastAPI application."""
    app = FastAPI(
        title="Sovereign AGI Control Plane [Workflow API]",
        description="V2 Architecture | Durable Workflows | Real-time Observability",
        version="13.04.1",
        lifespan=lifespan,
    )

    # Apply standardized middleware (CORS, Logging, OTel)
    configure_middleware(app)

    # Register routers
    app.include_router(workflow_router)

    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "version": "13.04.1",
            "environment": os.getenv("APP_ENV", "development")
        }

    return app

app = create_app()

if __name__ == "__main__":
    # Standard development port 8000
    uvicorn.run("services.workflow_api.main:app", host="0.0.0.0", port=8000, reload=True)
