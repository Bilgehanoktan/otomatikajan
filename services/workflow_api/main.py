
"""
services/workflow_api/main.py — Phase 13.04.1
Primary entry point for the Sovereign AGI Workflow Control Plane.
"""
from __future__ import annotations

import os
import time as _time
from datetime import datetime, timezone
from collections import deque
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect, Query, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
import uvicorn
import json

from libs.infra.lifespan import lifespan
from libs.infra.middleware import configure_middleware
from libs.infra.ws_manager import ws_manager
from libs.db.session import get_db, get_db_dep, AsyncSessionLocal
from services.workflow_api.router import router as workflow_router
from services.orchestration.application.sovereign_cortex import get_sovereign_cortex
from services.observability.logging import get_logger

# Phase 22 Integration: Mesh Observability & Actions
from services.observability import mesh_status_api, fleet_status_api
from services.governance import mesh_actions_api

# Phase 28 Integration: Autonomous Repair Lab
from services.workflow_api import repair_lab_router, governance_router

logger = get_logger("workflow_api")

def create_app() -> FastAPI:
    """Scaffold the FastAPI application."""
    app = FastAPI(
        title="Sovereign AGI | Mission Control",
        description="Sovereign AGI Governance Fabric & Autonomous Resilience Engine API",
        version="13.04.1",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        swagger_ui_parameters={"defaultModelsExpandDepth": -1}
    )

    # Apply standardized middleware (CORS, Logging, OTel)
    configure_middleware(app)

    # Register routers
    app.include_router(workflow_router)
    app.include_router(mesh_status_api.router)
    app.include_router(fleet_status_api.router, prefix="/api/v1")
    app.include_router(mesh_actions_api.router)
    app.include_router(repair_lab_router.router)
    app.include_router(governance_router.router)

    # Global Exception Handlers for JSON Stabilization
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.error(f"HTTP Error: {exc.detail} on {request.url.path}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "http_error",
                "detail": exc.detail,
                "path": request.url.path
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning(f"Validation Error: {exc.errors()} on {request.url.path}")
        return JSONResponse(
            status_code=422,
            content={
                "error": "validation_error",
                "detail": exc.errors(),
                "body": exc.body if hasattr(exc, "body") else None
            }
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.critical(f"UNHANDLED EXCEPTION: {str(exc)} on {request.url.path}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "detail": "Critical system failure occurred. Standardized JSON response enforced.",
                "type": type(exc).__name__,
                "msg": str(exc)
            }
        )

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def mission_control_home():
        """Sovereign Mission Control landing page."""
        template_path = os.path.join(os.path.dirname(__file__), "dashboard.html")
        if os.path.exists(template_path):
            return FileResponse(template_path)
        return HTMLResponse("<h1>Sovereign Mission Control</h1><p>Template not found.</p>")

    @app.get("/api/v1/health/dashboard")
    async def dashboard_stats(
        cortex=Depends(get_sovereign_cortex),
        db=Depends(get_db)
    ):
        t0 = _time.monotonic()
        result: dict = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "online",
        }

        # 1. Real Metrics from DB
        try:
            from sqlalchemy import select, func
            from libs.db.models.repair_models import RepairIncident, RepairProposal
            from libs.db.models.core_models import Project
            
            # Tasks running count
            tasks_res = await db.execute(select(func.count(Project.id)).where(Project.status == "running"))
            running_tasks = tasks_res.scalar() or 0
            
            # Approvals pending count
            approvals_res = await db.execute(select(func.count(RepairProposal.id)).where(RepairProposal.decision == "pending"))
            pending_apps = approvals_res.scalar() or 0
            
            # Failed tasks count
            failed_res = await db.execute(select(func.count(Project.id)).where(Project.status.in_(["error", "failed"])))
            failed_tasks = failed_res.scalar() or 0
            
            result["workflows"] = {
                "running": running_tasks,
                "pending_approval": pending_apps,
                "failed": failed_tasks
            }
            result["db_status"] = "connected"
        except Exception as e:
            logger.debug(f"Dashboard DB stats error: {e}")
            result["workflows"] = {"running": 0, "pending_approval": 0, "failed": 0}
            result["db_status"] = "degraded"

        # 2. Cortex Stats
        try:
            result["active_agents"] = len(cortex._agents) if hasattr(cortex, '_agents') else 0
            result["energy"] = 0.85 # Fallback
            if hasattr(cortex, 'affective_core') and hasattr(cortex.affective_core, 'get_energy'):
                 result["energy"] = await cortex.affective_core.get_energy()
        except Exception:
            result["active_agents"] = 0
            result["energy"] = 0.0

        # 3. Cost Summary
        try:
            from libs.llm.cost_tracker import cost_tracker
            summary = cost_tracker.summary()
            result["cost"] = {
                "total_usd": summary.get("total_cost_usd", 0.0),
                "budget_used_pct": summary.get("budget_used_pct", 0.0)
            }
        except Exception:
            result["cost"] = {"total_usd": 0.0, "budget_used_pct": 0.0}

        # 4. Phase 31: Governance & Rollout Metrics
        try:
            from libs.governance.launch_gatekeeper import LaunchGatekeeper
            # Note: This is a synthetic snapshot for the dashboard
            passed, gate_details = await LaunchGatekeeper.validate_for_rollout()
            result["governance"] = {
                "rollout_ready": passed,
                "constitutional_locks": gate_details.get("governance", {}).get("internal_guards_active", False),
                "quorum_status": gate_details.get("quorum", {}).get("status", "N/A"),
                "pending_approvals": gate_details.get("quorum", {}).get("pending_critical_signoffs", 0)
            }
            
            # Simulated Canary Confidence
            result["canary"] = {
                "success_rate": gate_details.get("accuracy", {}).get("score", 0.0) * 100,
                "promoted": 4,
                "total_patches_7d": 12
            }
            
            result["health_score"] = 92 if passed else 75
            result["health_label"] = "OPTIMAL" if passed else "DEGRADED"
            
        except Exception as e:
            logger.error(f"Governance metrics error: {e}")
            result["governance"] = {"rollout_ready": False}

        result["api_latency_ms"] = round((_time.monotonic() - t0) * 1000, 1)
        return result

    @app.get("/api/v1/health/evolution")
    async def evolution_timeline(db=Depends(get_db)):
        """Fetch real autonomous repair events for the evolution timeline."""
        events = []
        try:
            from sqlalchemy import select, desc
            from libs.db.models.repair_models import RepairIncident, RepairTournament, RepairPatchLog
            
            # 1. Latest Incidents (Diagnosis)
            inc_res = await db.execute(select(RepairIncident).order_by(desc(RepairIncident.first_seen_at)).limit(3))
            for inc in inc_res.scalars():
                events.append({
                    "title": "Sistem Teşhisi",
                    "desc": f"{inc.service} servisinde {inc.severity} seviye anomali.",
                    "time": inc.first_seen_at.isoformat(),
                    "type": "diagnosis",
                    "evidence": f"INC-{inc.incident_id[:8]}"
                })

            # 2. Latest Tournaments (Scientific Tournament)
            tourn_res = await db.execute(select(RepairTournament).order_by(desc(RepairTournament.created_at)).limit(3))
            for tourn in tourn_res.scalars():
                events.append({
                    "title": "Bilimsel Turnuva",
                    "desc": f"{tourn.total_candidates} aday tamir stratejisi yarıştırılıyor.",
                    "time": tourn.created_at.isoformat(),
                    "type": "tournament",
                    "info": f"SCORE: {tourn.winner_score:.2f}"
                })

            # 3. Latest Patches (Promotion)
            patch_res = await db.execute(select(RepairPatchLog).order_by(desc(RepairPatchLog.recorded_at)).limit(3))
            for patch in patch_res.scalars():
                events.append({
                    "title": "Üretim Terfisi",
                    "desc": f"Sistem {patch.classification} yaması ile güncellendi.",
                    "time": patch.recorded_at.isoformat(),
                    "type": "promotion",
                    "status": patch.outcome.upper()
                })

            # Default if empty
            if not events:
                events = [{ "title": "Sistem Hazır", "desc": "Çekirdek kernel stabil ve gözlem altında.", "time": datetime.now(timezone.utc).isoformat(), "type": "diagnosis", "evidence": "BOOT-OK" }]

            # Sort all by time
            events.sort(key=lambda x: x["time"], reverse=True)
            
        except Exception as e:
            logger.error(f"Evolution timeline fetch error: {e}")
            events = [{ "title": "Telemetri Hatası", "desc": "Evrim verileri şu an alınamıyor.", "time": datetime.now(timezone.utc).isoformat(), "type": "diagnosis", "evidence": "DB-ERR" }]

        return events[:10]

    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "version": "14.02",
            "environment": os.getenv("APP_ENV", "development")
        }

    # Severity veategori haritalama
    _EVENT_SEVERITY_MAP = {
        "WORKFLOW_STARTED":   ("info",     "workflow"),
        "WORKFLOW_COMPLETED": ("info",     "workflow"),
        "WORKFLOW_FAILED":    ("critical", "failover"),
        "STEP_STARTED":       ("info",     "workflow"),
        "STEP_COMPLETED":     ("info",     "workflow"),
        "BUDGET_WARNING":     ("warning",  "budget"),
        "GOVERNANCE_ALERT":   ("critical", "governance"),
        "SYSTEM_INFO":        ("info",     "alert"),
    }

    # Logging Ring Buffer
    EVENT_RING = deque(maxlen=200)
    _event_seq = 0

    def push_event(etype: str, message: str = "", severity: str = "info", raw: dict = None):
        """Ring buffer'a yerelleştirilmiş olay ekle."""
        nonlocal _event_seq
        _event_seq += 1
        
        # Otomatik haritalama
        if etype in _EVENT_SEVERITY_MAP:
             severity, _ = _EVENT_SEVERITY_MAP[etype]

        event = {
            "seq": _event_seq,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": etype,
            "severity": severity,
            "message": message or f"Sistem Olayı: {etype}",
            "raw": raw or {}
        }
        EVENT_RING.append(event)
        # Broadcast via ws_manager (if global context allows)
        try:
            import asyncio
            loop = asyncio.get_running_loop()
            if loop.is_running():
                asyncio.create_task(ws_manager.broadcast(json.dumps(event)))
        except RuntimeError:
            # No loop running, skip broadcast
            pass
        return event

    # Initial boot event
    push_event("SYSTEM_INFO", "Egemen YAZ Master Kontrol Başlatıldı", "info")

    @app.get("/api/v1/events/stream")
    async def get_events_stream(
        since_seq: int = Query(0),
        limit: int = Query(50)
    ):
        """Durable polling fallback for the event stream."""
        events = [e for e in list(EVENT_RING) if e["seq"] > since_seq]
        return {"events": events[:limit]}

    @app.websocket("/ws/events")
    async def websocket_events(websocket: WebSocket):
        await ws_manager.connect(websocket)
        try:
            # Send backlog
            for event in list(EVENT_RING):
                await websocket.send_text(json.dumps(event))
            while True:
                # Keep alive
                await websocket.receive_text()
        except WebSocketDisconnect:
            ws_manager.disconnect(websocket)

    return app

app = create_app()

if __name__ == "__main__":
    uvicorn.run("services.workflow_api.main:app", host="0.0.0.0", port=8000, reload=True)
