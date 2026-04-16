"""
services/workflow_api/main.py — Phase 13.04
Primary entry point for the Sovereign AGI Workflow Control Plane.
"""
from __future__ import annotations

import os
from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect
import uvicorn

from libs.infra.lifespan import lifespan
from libs.infra.middleware import configure_middleware
from libs.infra.ws_manager import ws_manager
from services.workflow_api.router import router as workflow_router
from services.orchestration.application.sovereign_cortex import get_sovereign_cortex
from services.observability.logging import get_logger

# Phase 22 Integration: Mesh Observability & Actions
from services.observability import mesh_status_api, fleet_status_api
from services.governance import mesh_actions_api

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
    app.include_router(mesh_status_api.router)
    app.include_router(fleet_status_api.router, prefix="/api/v1")
    app.include_router(mesh_actions_api.router)

    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "version": "13.04.1",
            "environment": os.getenv("APP_ENV", "development")
        }

    @app.get("/workflows")
    async def list_workflows(cortex=Depends(get_sovereign_cortex)):
        """Refine dataprovider format: { data: [...] }"""
        # Simply list active workflow instances if available
        # For now, return mock/empty list if db is not populated
        return {"data": []}

    @app.websocket("/ws")
    @app.websocket("/ws/logs")
    async def websocket_endpoint(websocket: WebSocket):
        await ws_manager.connect(websocket)
        try:
            while True:
                await websocket.receive_text() # Keep connection alive
        except WebSocketDisconnect:
            ws_manager.disconnect(websocket)

    return app

app = create_app()

if __name__ == "__main__":
    # Standard development port 8000
    uvicorn.run("services.workflow_api.main:app", host="0.0.0.0", port=8000, reload=True)
