import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from services.workflow_api.router import router as workflow_router
from services.workflow_api.governance_router import router as governance_router
from services.workflow_api.repair_lab_router import router as repair_lab_router
from services.workflow_api.metrics_router import router as metrics_router
from services.workflow_api.health_router import router as health_router, websocket_endpoint
from services.auth.router import router as auth_router
from services.observability.fleet_status_api import router as fleet_router
from libs.db.session import init_db

app = FastAPI(
    title="Sovereign AGI Workflow API",
    description="Mission Control Plane for Autonomous Governance & Repair",
    version="12.1.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(workflow_router, prefix="/api/v1")
app.include_router(governance_router, prefix="/api/v1/governance")
app.include_router(repair_lab_router, prefix="/api/v1")
app.include_router(metrics_router, prefix="/api/v1/metrics")
app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1/auth")
app.include_router(fleet_router, prefix="/api/v1")

@app.websocket("/ws/events")
async def websocket_route(websocket: WebSocket):
    await websocket_endpoint(websocket)

@app.on_event("startup")
async def startup_event():
    print("Sovereign AGI Workflow API starting up...")
    await init_db()
    print("Database Initialized.")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "workflow_api"}

if __name__ == "__main__":
    uvicorn.run("services.workflow_api.main:app", host="0.0.0.0", port=8000, reload=True)