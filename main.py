"""
AI Yazılım Şirketi — Ana Uygulama
Modülerleştirilmiş Versiyon: Tüm başlatma mantığı startup/ paketinde.
"""
APP_VERSION = "4.0.0-RC1.4"

import asyncio
import json
import os
import sys
from datetime import datetime, timezone

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

# ── .env otomatik yükle ───────────────────────────────────
try:
    from dotenv import load_dotenv as _load_dotenv
    if os.path.exists(".env"):
        _load_dotenv(".env", override=False)
    if os.path.exists(".env.local"):
        _load_dotenv(".env.local", override=False)
    env = os.getenv("APP_ENV", os.getenv("ENVIRONMENT", "development"))
    if env != "production" and not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            _load_dotenv(".env.example", override=True)
except ImportError:
    pass

# ── Güvenlik çekirdek kontrolleri ─────────────────────────
from config import APP_ENV as _ENV, ADMIN_SECRET, JWT_SECRET

if _ENV == "production":
    # FAZ 12 HARDENING: Üretim ortamında zayıf veya şablon sırları KESİNLİKLE reddet.
    WEAK_TEMPLATES = ["REPLACE_WITH", "your-secret", "changeme", "123456"]
    
    missing = [k for k, v in [("ADMIN_SECRET", ADMIN_SECRET), ("JWT_SECRET", JWT_SECRET)] if not v]
    if missing:
        print(f"HATA: Üretim sırları eksik: {missing}")
        sys.exit(1)
        
    for name, secret in [("ADMIN_SECRET", ADMIN_SECRET), ("JWT_SECRET", JWT_SECRET)]:
        is_weak = any(tpl in secret for tpl in WEAK_TEMPLATES)
        is_low_entropy = len(set(secret)) < 8
        if is_weak or is_low_entropy:
            reason = "Template eşleşmesi" if is_weak else "Düşük entropi"
            print(f"HATA: {name} üretim ortamı için kabul edilemez! Neden: {reason}")
            sys.exit(1)

    if JWT_SECRET and len(JWT_SECRET) < 64:
        print("HATA: JWT_SECRET üretim ortamı için çok kısa (en az 64 karakter olmalı).")
        sys.exit(1)

# ── Core singleton'ları ───────────────────────────────────
from core.agi.cognitive.sovereign_cortex import sovereign_cortex as orchestrator
from core.agi.governance.watchdog import governance_watchdog
from core.heal_engine import heal_engine
from core.events import event_bus
from core.job_queue import job_queue
from api.ws_manager import ws_manager
from observability.logging import get_logger
from observability.metrics import metrics

logger = get_logger("main")

# ── Startup modülleri ─────────────────────────────────────
from startup.lifespan import lifespan, register_event_listeners
from startup.middleware import configure_middleware
from startup.routers import register_routers

# Event bus dinleyicilerini kaydet (modül yüklenirken)
register_event_listeners()

# ── Uygulama Tanımı ──────────────────────────────────────
app = FastAPI(
    title="Otonom Yazilim Gelistirme Sirketi",
    description="V2 Mimari | 8 Ajan | DAG Motoru | Öz-İyileştirme",
    version=APP_VERSION,
    lifespan=lifespan,
)

configure_middleware(app)
register_routers(app)

# ── Dashboard (Statik) ───────────────────────────────────
_dash = os.path.join(os.path.dirname(__file__), "dashboard")
if os.path.isdir(_dash):
    app.mount("/static", StaticFiles(directory=_dash), name="static")
    _up = "uploads"
    if not os.path.exists(_up):
        os.makedirs(_up)
    app.mount("/uploads", StaticFiles(directory=_up), name="uploads")

    @app.get("/", include_in_schema=False)
    async def serve_dashboard():
        return FileResponse(
            os.path.join(_dash, "index.html"),
            headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"},
        )


# ── WebSocket ─────────────────────────────────────────────
@app.websocket("/ws/logs")
async def websocket_logs(ws: WebSocket):
    # Faz 12.1 Security: WebSocket Authentication
    token = ws.query_params.get("token")
    if not token:
        # Alt-metot: Sec-WebSocket-Protocol veya Authorization Header
        token = ws.headers.get("authorization", "").replace("Bearer ", "")
    
    if not token:
        # 3. Öncelik: Cookie (access_token) - Dashboard uyumluluğu için
        token = ws.cookies.get("access_token")

    if not token:
        await ws.accept()
        await ws.send_text(json.dumps({"error": "Unauthorized", "code": 4001, "message": "WebSocket için yetkilendirme (token/cookie) gerekli."}))
        await ws.close(code=4001)
        return

    try:
        from auth.jwt_auth import _decode_token
        payload = _decode_token(token)
        if payload.get("type") != "access":
            await ws.accept()
            await ws.send_text(json.dumps({"error": "Invalid token type", "code": 4002}))
            await ws.close(code=4002)
            return
    except Exception:
        await ws.accept()
        await ws.send_text(json.dumps({"error": "Authentication failed", "code": 4003}))
        await ws.close(code=4003)
        return

    await ws_manager.connect(ws)
    for evt in event_bus.recent(20):
        try:
            await ws.send_text(json.dumps(evt, default=str))
        except Exception:
            break
    try:
        while True:
            data = await ws.receive_text()
            if data == "ping":
                await ws.send_text(json.dumps({"event": "pong", "timestamp": datetime.now(timezone.utc).isoformat()}))
    except Exception:
        pass
    finally:
        ws_manager.disconnect(ws)


# ── Sistem Endpoint'leri ──────────────────────────────────
@app.get("/health", tags=["Sistem"])
@app.get("/api/v1/health", tags=["Sistem"], include_in_schema=False)
async def health_check():
    from db.session import is_db_available, db_error
    from core.agency.loader import agency_loader
    from observability.memory_governor import memory_governor
    
    db_ok = await is_db_available()
    current_agents = len(orchestrator._agents) if hasattr(orchestrator, "_agents") else 0
    specialists = len(agency_loader.agents)
    mem_usage = memory_governor.get_current_usage_mb()

    return {
        "status": "degraded" if (not db_ok or mem_usage > memory_governor.MAX_MEMORY_MB) else "ok",
        "reason": "memory_limit_exceeded" if mem_usage > memory_governor.MAX_MEMORY_MB else ("db_failed" if not db_ok else None),
        "version": APP_VERSION,
        "env": _ENV,
        "agents": current_agents,
        "specialists": specialists,
        "memory": {
            "current_mb": round(mem_usage, 2),
            "limit_mb": memory_governor.MAX_MEMORY_MB,
            "status": "warning" if mem_usage > memory_governor.WARNING_MEMORY_MB else "healthy"
        },
        "heal_score": heal_engine.system_health_score() if hasattr(heal_engine, "system_health_score") else 1.0,
        "ws_clients": ws_manager.client_count,
        "db": {"available": db_ok, "error": db_error() if not db_ok else ""},
        "queue": {
            "backend": getattr(job_queue, "backend_name", "unknown"),
            "supports_registration": getattr(job_queue, "supports_registration", False),
        },
        "repair": _get_repair_health_summary(),
        "governance": {
            "health_score": round(governance_watchdog.health_score, 2),
            "instinct_count": governance_watchdog.instinct_count,
            "prevented_count": governance_watchdog.prevented_count,
            "is_auditing": True,
            "status": "healthy" if governance_watchdog.health_score > 0.8 else "warning"
        },
        "timestamp": datetime.now(timezone.utc),
    }


@app.get("/health/diagnostics", tags=["Sistem"])
async def advanced_health():
    from db.session import is_db_available
    db_ok = await is_db_available()
    all_tasks = asyncio.all_tasks()
    active_watchdogs = [t.get_name() for t in all_tasks if "Watchdog" in t.get_name() or "Controller" in t.get_name()]

    return {
        "status": "healthy" if db_ok else "unhealthy",
        "orchestrator_ready": orchestrator.agent_count() > 0,
        "active_watchdogs": active_watchdogs,
        "memory_usage": _get_process_memory(),
        "db_status": "connected" if db_ok else "disconnected",
        "timestamp": datetime.now(timezone.utc),
    }


@app.get("/health/deep", tags=["Sistem"])
async def deep_health_check():
    active_tasks = [
        t.get_name()
        for t in asyncio.all_tasks()
        if "metabolism" in t.get_name() or "governor" in t.get_name() or "supervisor" in t.get_name()
    ]
    required = ["metabolism_loop", "memory_governor"]
    missing_tasks = [r for r in required if not any(r in task_name for task_name in active_tasks)]
    
    if missing_tasks:
        logger.warning(f"Derin Sağlık Kontrolü Başarısız: Eksik AML görevleri -> {missing_tasks}")
        return JSONResponse(status_code=503, content={"status": "degraded", "missing": missing_tasks})

    return {"status": "healthy", "active_aml_tasks": active_tasks, "timestamp": datetime.now().isoformat()}


@app.get("/metrics", tags=["Sistem"])
async def get_metrics():
    return metrics.snapshot()


# ── Yardımcılar ───────────────────────────────────────────
def _get_process_memory() -> str:
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return f"{process.memory_info().rss / 1024 / 1024:.2f} MB"
    except ImportError:
        return "N/A (psutil missing)"


def _get_repair_health_summary() -> dict:
    try:
        from core.repair_orchestrator import get_repair_orchestrator
        orch = get_repair_orchestrator(model_orch=getattr(orchestrator, "model_orch", None))
        stats = orch.stats()
        return {
            "total_jobs": stats.get("total", 0),
            "open_incidents": stats.get("incident_memory", {}).get("open", 0),
            "pr_pending": stats.get("pipeline", {}).get("by_status", {}).get("awaiting_approval", 0),
        }
    except Exception:
        return {"available": False}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Yakalanmamis hata: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Dahili sunucu hatası",
            "code": "INTERNAL_ERROR",
            "detail": str(exc) if _ENV == "development" else "Gizlendi",
        },
    )
