"""
services/workflow_api/main.py — Phase 13.04
Primary entry point for the Sovereign AGI Workflow Control Plane.
"""
from __future__ import annotations

import os
from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
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

# Phase 28 Integration: Autonomous Repair Lab
from services.workflow_api import repair_lab_router, governance_router

logger = get_logger("workflow_api")

def create_app() -> FastAPI:
    """Scaffold the FastAPI application."""
    app = FastAPI(
        title="Sovereign AGI | Mission Control",
        description="Core Governance Fabric & Autonomous Resilience Engine",
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

    @app.get("/", response_class=HTMLResponse)
    async def mission_control_home():
        """Sovereign Mission Control landing page."""
        template_path = os.path.join(os.path.dirname(__file__), "dashboard.html")
        if os.path.exists(template_path):
            return FileResponse(template_path)
        return HTMLResponse("<h1>Sovereign Mission Control</h1><p>Template not found.</p>")

    @app.get("/api/v1/health/dashboard")
    async def dashboard_stats(cortex=Depends(get_sovereign_cortex)):
        """
        Faz 2 — Birleşik Canlı Sağlık Özeti.
        Tüm Mission Control KPI'larını tek çağrıda döndürür.
        Polling aralığı: 5-10 saniye arası önerilir.
        """
        import time as _time
        from datetime import datetime, timezone

        t0 = _time.monotonic()
        result: dict = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "online",
        }

        # ── 1. Workflow İstatistikleri ───────────────────────
        try:
            from libs.db.session import AsyncSessionLocal
            from libs.db.models.core_models import Project, ProjectStatus
            from sqlalchemy import select, func

            async with AsyncSessionLocal() as db:
                rows = (await db.execute(
                    select(Project.status, func.count(Project.id).label("cnt"))
                    .group_by(Project.status)
                )).all()

            counts = {}
            for row in rows:
                s = row.status.value if hasattr(row.status, "value") else str(row.status)
                counts[s.lower()] = row.cnt

            total     = sum(counts.values())
            running   = counts.get("running", 0)
            completed = counts.get("completed", 0) + counts.get("partial_complete", 0)
            failed    = counts.get("error", 0) + counts.get("failed", 0)
            pending   = counts.get("pending", 0) + counts.get("queued", 0)
            pending_approval = counts.get("pending_approval", 0)
            success_rate = round(completed / max(completed + failed, 1) * 100, 1)

            result["workflows"] = {
                "total": total,
                "running": running,
                "completed": completed,
                "failed": failed,
                "pending": pending,
                "pending_approval": pending_approval,
                "success_rate_pct": success_rate,
            }
            result["db_status"] = "connected"
        except Exception as e:
            logger.warning(f"Workflow stats unavailable: {e}")
            result["workflows"] = {
                "total": 0, "running": 0, "completed": 0, "failed": 0,
                "pending": 0, "pending_approval": 0, "success_rate_pct": 0,
            }
            result["db_status"] = "disconnected"

        # ── 2. Sistem Sağlık Skoru ──────────────────────────
        # Bileşik skor: workflow başarı oranı (%40), DB bağlantı (%20),
        # canary (%20), bütçe (%20)
        health_factors = []

        wf_health = result["workflows"]["success_rate_pct"]
        health_factors.append(("workflow", min(wf_health, 100)))

        db_health = 100 if result["db_status"] == "connected" else 0
        health_factors.append(("db", db_health))

        # ── 3. Aktif Ajan/Birim ─────────────────────────────
        try:
            active_agents = len(cortex.agents) if hasattr(cortex, 'agents') else 0
        except Exception:
            active_agents = 0
        result["active_agents"] = active_agents

        # ── 4. Operasyon Maliyeti ───────────────────────────
        try:
            from libs.llm.cost_tracker import cost_tracker
            cost_summary = cost_tracker.summary()
            result["cost"] = {
                "total_usd": cost_summary["total_cost_usd"],
                "budget_usd": cost_summary["budget_usd"],
                "budget_used_pct": cost_summary["budget_used_pct"],
                "total_calls": cost_summary["total_calls"],
                "avg_latency_s": cost_summary["avg_latency_s"],
            }
            budget_health = max(0, 100 - cost_summary["budget_used_pct"])
            health_factors.append(("budget", budget_health))
        except Exception as e:
            logger.debug(f"Cost tracker unavailable: {e}")
            result["cost"] = {
                "total_usd": 0.0, "budget_usd": 100.0,
                "budget_used_pct": 0.0, "total_calls": 0, "avg_latency_s": 0.0,
            }
            health_factors.append(("budget", 100))

        # ── 5. Canary Başarısı ──────────────────────────────
        try:
            async with AsyncSessionLocal() as db:
                from services.improve.metrics_service import ImprovementMetricsService
                svc = ImprovementMetricsService(db)
                canary = await svc.get_canary_stats(days=7)
            result["canary"] = {
                "success_rate": canary["success_rate"],
                "active_canary": canary["active_canary"],
                "total_patches_7d": canary["total_patches"],
                "promoted": canary["promoted"],
                "rolled_back": canary["rolled_back"],
            }
            canary_health = canary["success_rate"] if canary["total_patches"] > 0 else 100
            health_factors.append(("canary", canary_health))
        except Exception as e:
            logger.debug(f"Canary stats unavailable: {e}")
            result["canary"] = {
                "success_rate": 0, "active_canary": 0,
                "total_patches_7d": 0, "promoted": 0, "rolled_back": 0,
            }
            health_factors.append(("canary", 100))

        # ── 6. Sağlık Skoru Hesapla ─────────────────────────
        weights = {"workflow": 0.40, "db": 0.20, "canary": 0.20, "budget": 0.20}
        health_score = sum(
            weights.get(name, 0) * score for name, score in health_factors
        )
        health_score = round(min(max(health_score, 0), 100), 1)

        if health_score >= 80:
            health_label = "healthy"
        elif health_score >= 60:
            health_label = "degraded"
        else:
            health_label = "critical"

        result["health_score"] = health_score
        result["health_label"] = health_label
        result["status"] = "online" if result["db_status"] == "connected" else "degraded"

        # ── 7. API Gecikme (bu endpoint'in kendi yanıt süresi) ──
        api_latency_ms = round((_time.monotonic() - t0) * 1000, 1)
        result["api_latency_ms"] = api_latency_ms

        return result

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
        return {"data": []}

    # ── Faz 3: Event Stream (Ring Buffer + Polling + WS) ────────
    import time as _time
    from datetime import datetime, timezone
    from collections import deque
    import json

    # Severity ve kategori haritalama
    _EVENT_SEVERITY_MAP = {
        "WORKFLOW_STARTED":   ("info",     "workflow"),
        "WORKFLOW_COMPLETED": ("info",     "workflow"),
        "WORKFLOW_FAILED":    ("critical", "failover"),
        "STEP_STARTED":       ("info",     "workflow"),
        "STEP_COMPLETED":     ("info",     "workflow"),
        "STEP_FAILED":        ("warning",  "failover"),
        "TOOL_STARTED":       ("info",     "workflow"),
        "TOOL_COMPLETED":     ("info",     "workflow"),
        "TOOL_FAILED":        ("warning",  "repair"),
        "BUDGET_WARNING":     ("warning",  "budget"),
        "BUDGET_EXCEEDED":    ("critical", "budget"),
        "APPROVAL_REQUIRED":  ("warning",  "quorum"),
        "APPROVAL_GRANTED":   ("info",     "quorum"),
        "GOVERNANCE_ALERT":   ("critical", "governance"),
        "CANARY_PASSED":      ("info",     "repair"),
        "CANARY_FAILED":      ("critical", "repair"),
        "HEALTH_DEGRADED":    ("warning",  "alert"),
        "HEALTH_CRITICAL":    ("critical", "alert"),
        "SYSTEM_INFO":        ("info",     "alert"),
    }

    # Ring buffer — son 200 olayı tutar
    _event_ring: deque = deque(maxlen=200)
    _event_seq: int = 0

    def _push_event(event: dict):
        """Ring buffer'a olay ekle."""
        nonlocal _event_seq
        _event_seq += 1
        etype = event.get("type", "UNKNOWN")
        severity, category = _EVENT_SEVERITY_MAP.get(etype, ("info", "alert"))
        enriched = {
            "seq": _event_seq,
            "timestamp": event.get("timestamp", datetime.now(timezone.utc).isoformat()),
            "type": etype,
            "severity": severity,
            "category": category,
            "message": _format_event_message(event),
            "raw": event,
        }
        _event_ring.append(enriched)
        return enriched

    def _format_event_message(event: dict) -> str:
        """Olayı okunabilir Türkçe mesaja çevir."""
        t = event.get("type", "")
        pid = str(event.get("project_id", event.get("workflow_id", "")))[:8]
        step = event.get("step_name", event.get("tool_name", ""))
        err = event.get("error", "")

        messages = {
            "WORKFLOW_STARTED":   f"İş akışı başlatıldı [{pid}]",
            "WORKFLOW_COMPLETED": f"İş akışı tamamlandı [{pid}]",
            "WORKFLOW_FAILED":    f"İş akışı BAŞARISIZ [{pid}]",
            "STEP_STARTED":       f"Adım başladı: {step} [{pid}]",
            "STEP_COMPLETED":     f"Adım tamamlandı: {step} [{pid}]",
            "STEP_FAILED":        f"Adım başarısız: {step} — {err[:80]}",
            "TOOL_STARTED":       f"Araç çalıştırılıyor: {step}",
            "TOOL_COMPLETED":     f"Araç başarılı: {step}",
            "TOOL_FAILED":        f"Araç hatası: {step} — {err[:80]}",
            "BUDGET_WARNING":     f"Bütçe uyarısı — limit yaklaşıyor",
            "BUDGET_EXCEEDED":    f"BÜTÇE AŞILDI — operasyon durduruldu",
            "APPROVAL_REQUIRED":  f"Onay gerekli: {step} [{pid}]",
            "APPROVAL_GRANTED":   f"Onay verildi: [{pid}]",
            "GOVERNANCE_ALERT":   f"Yönetişim uyarısı: {event.get('message', '')}",
            "CANARY_PASSED":      f"Canary doğrulaması başarılı [{pid}]",
            "CANARY_FAILED":      f"Canary doğrulaması BAŞARISIZ [{pid}]",
            "HEALTH_DEGRADED":    f"Sistem sağlığı bozuldu",
            "HEALTH_CRITICAL":    f"SİSTEM KRİTİK DURUMDA",
            "SYSTEM_INFO":        event.get("message", "Sistem bilgisi"),
        }
        return messages.get(t, f"{t}: {event.get('message', json.dumps(event)[:100])}")

    # ws_manager.broadcast'i sarmalayarak ring buffer'a da yaz
    _original_broadcast = ws_manager.broadcast

    async def _broadcast_with_ring(message: dict | str):
        if isinstance(message, str):
            try:
                msg_dict = json.loads(message)
            except Exception:
                msg_dict = {"type": "RAW", "message": message[:200]}
        else:
            msg_dict = message
        _push_event(msg_dict)
        await _original_broadcast(message)

    ws_manager.broadcast = _broadcast_with_ring

    # Başlangıç olayları
    _push_event({"type": "SYSTEM_INFO", "message": "Mission Control başlatıldı", "timestamp": datetime.now(timezone.utc).isoformat()})
    _push_event({"type": "SYSTEM_INFO", "message": "Event stream aktif — ring buffer: 200 slot", "timestamp": datetime.now(timezone.utc).isoformat()})

    @app.get("/api/v1/events/stream")
    async def event_stream(since_seq: int = 0, limit: int = 50):
        """
        Faz 3 — Polling fallback: son olayları döndürür.
        ?since_seq=N ile sadece N'den sonraki olaylar gelir.
        """
        events = [e for e in _event_ring if e["seq"] > since_seq]
        # En son 'limit' olayı döndür
        events = events[-limit:]
        return {
            "events": events,
            "latest_seq": events[-1]["seq"] if events else since_seq,
            "total_buffered": len(_event_ring),
        }

    @app.websocket("/ws/events")
    async def websocket_events(websocket: WebSocket):
        """
        Faz 3 — WebSocket event kanalı.
        Bağlantı kurulunca son 30 olayı gönderir, sonra canlı akış.
        """
        await ws_manager.connect(websocket)
        try:
            # Replay son 30 olayı
            recent = list(_event_ring)[-30:]
            for event in recent:
                await websocket.send_text(json.dumps(event))

            # Canlı akış: yeni olaylar geldiğinde broadcast üzerinden otomatik
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            ws_manager.disconnect(websocket)

    @app.websocket("/ws")
    @app.websocket("/ws/logs")
    async def websocket_endpoint(websocket: WebSocket):
        await ws_manager.connect(websocket)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            ws_manager.disconnect(websocket)

    return app

app = create_app()

if __name__ == "__main__":
    # Standard development port 8000
    uvicorn.run("services.workflow_api.main:app", host="0.0.0.0", port=8000, reload=True)
