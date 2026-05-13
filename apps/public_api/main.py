print("[DEBUG] Main.py is being loaded...")
"""
AI Yazılım Şirketi — Ana Uygulama
Modülerleştirilmiş Versiyon: Tüm başlatma mantığı startup/ paketinde.
"""
APP_VERSION = "4.0.0-RC1.7"

import asyncio
import json
import os
import sys
from pathlib import Path

# Project root path (3 levels up from apps/api/main.py)
ROOT_DIR = str(Path(__file__).resolve().parents[2])
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)


from datetime import datetime, timezone

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

print("[DEBUG] Environment loading...")
# ── .env otomatik yükle ───────────────────────────────────
try:
    from dotenv import load_dotenv as _load_dotenv
    _in_container = os.path.exists("/.dockerenv") or os.getenv("DOCKER_CONTAINER", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    _dotenv_override = not _in_container
    if os.path.exists(".env"):
        _load_dotenv(".env", override=_dotenv_override)
    if os.path.exists(".env.local"):
        try:
            _load_dotenv(".env.local", override=False)
        except UnicodeDecodeError:
            # .env.local dosyası bozuk encoding ile kaydedilmiş (UTF-16 BOM vb.)
            # Sessizce atla, .env yeterli olacak.
            pass
    env = os.getenv("APP_ENV", os.getenv("ENVIRONMENT", "development"))
    if env != "production" and not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            _load_dotenv(".env.example", override=_dotenv_override)
except ImportError:
    pass

# ── Güvenlik çekirdek kontrolleri ─────────────────────────
from libs.config import APP_ENV as _ENV, APP_UI_MODE, ADMIN_SECRET, JWT_SECRET, validate_production_config
from services.observability.logging import get_logger

logger = get_logger("main")

if _ENV == "production":
    try:
        validate_production_config()
        logger.info("[SECURITY] Production environment validation passed.")
    except RuntimeError as e:
        print(f"KRİTİK GÜVENLİK HATASI: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"BEKLENMEDİK KURULUM HATASI: {e}")
        sys.exit(1)


# ── Core singleton'ları (Dinamik Yükleme için Kaldırıldı) ───────────
# Not: orchestrator, governance_watchdog vb. artık fonksiyon bazında import ediliyor.

print("[DEBUG] Middleware & Router setup...")
# ── Startup modülleri ─────────────────────────────────────
print("[DEBUG] Loading lifespan...")
from libs.infra.lifespan import lifespan, register_event_listeners
print("[DEBUG] Loading middleware config...")
from libs.infra.middleware import configure_middleware
print("[DEBUG] Loading router registry...")
from libs.infra.router_registry import register_routers
print("[DEBUG] All infra modules loaded.")

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
print("[DEBUG] Registering routers...")
register_routers(app)
print("[DEBUG] Routers registered.")

# ── Route Debugging (Phase 13.05) ─────────────────────────
if os.getenv("DEBUG_ROUTES", "false").lower() == "true":
    logger.info("--- REGISTERED ROUTES ---")
    for route in app.routes:
        if hasattr(route, 'path'):
            logger.info(f"[ROUTE] {getattr(route, 'methods', 'ANY')} {route.path}")
    logger.info("--- END ROUTES ---")

# ── OTel Tracing Middleware (Phase 13.04) ─────────────────
try:
    from libs.observability.middleware import get_otel_middleware
    _OTelMW = get_otel_middleware()
    if _OTelMW is not None:
        app.add_middleware(_OTelMW)
        logger.info("[OTEL] Tracing middleware registered")
except Exception as _otel_err:
    logger.warning(f"[OTEL] Middleware skipped: {_otel_err}")

# ── Incident capturing Middleware (Phase 16) ──────────────
try:
    from libs.observability.incident_middleware import SovereignIncidentMiddleware
    app.add_middleware(SovereignIncidentMiddleware)
    logger.info("[INCIDENT] Sovereign Incident Middleware registered")
except Exception as _inc_err:
    logger.error(f"[INCIDENT] Middleware failed: {_inc_err}")


# ── Dashboard & Control Plane (Unified Routing) ───────────
_dash_legacy = os.path.join(ROOT_DIR, "hub_interaction", "dashboard")
_dash_modern = os.path.join(ROOT_DIR, "apps", "refine_control_plane", "out")

# Prioritize Modern Control Plane
_active_dash = _dash_modern if os.path.exists(os.path.join(_dash_modern, "index.html")) else _dash_legacy
_dashboard_static_enabled = APP_UI_MODE == "static"

_up = "uploads"
if not os.path.exists(_up):
    os.makedirs(_up)
app.mount("/uploads", StaticFiles(directory=_up), name="uploads")

if _dashboard_static_enabled and os.path.isdir(_active_dash):
    # 1. Mount the whole directory under /static for general access
    app.mount("/static", StaticFiles(directory=_active_dash), name="static")

    # 2. Specifically mount /_next for Next.js internal assets
    _next_dir = os.path.join(_active_dash, "_next")
    if os.path.exists(_next_dir):
        app.mount("/_next", StaticFiles(directory=_next_dir), name="next_assets")
        logger.info(f"[DASHBOARD] Next.js assets mounted from {_next_dir}")

    logger.info(
        f"[DASHBOARD] UI mode=static. Active Dashboard "
        f"({'Modern' if _active_dash == _dash_modern else 'Legacy'}) served from {_active_dash}"
    )
elif _dashboard_static_enabled:
    logger.warning("[DASHBOARD] No dashboard directory found. Root / will 404.")
else:
    logger.info("[DASHBOARD] UI mode=api-only. Static dashboard serving disabled; use port 3100 for the control plane.")

# ── Workflow Control Plane API (Centralized in router_registry) ───────────
# Removed manual inclusion to prevent duplicate routes and conflicts.
# The following is handled by register_routers(app) above.



# ── WebSocket ─────────────────────────────────────────────
async def _authenticated_websocket_stream(ws: WebSocket):
    from libs.infra.ws_manager import ws_manager
    from services.orchestration.domain.events import event_bus
    
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
        from services.auth.jwt_auth import _decode_token
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
    
    # Faz 12.1: Populate with actual historical events from DecisionLineage if available
    try:
        from libs.db.session import AsyncSessionLocal
        from sqlalchemy import select, desc
        from libs.db.models.lineage_models import DecisionLineage
        
        async with AsyncSessionLocal() as db:
            q = select(DecisionLineage).order_by(desc(DecisionLineage.created_at)).limit(25)
            res = await db.execute(q)
            items = res.scalars().all()
            
            for i in reversed(items):
                sev = "info"
                if "FAIL" in (i.outcome or "").upper() or "ERROR" in (i.rationale or "").upper():
                    sev = "critical"
                elif "WARN" in (i.rationale or "").upper():
                    sev = "warning"
                
                await ws.send_text(json.dumps({
                    "seq": int(i.created_at.timestamp() * 1000) if i.created_at else 0,
                    "timestamp": i.created_at.isoformat() if i.created_at else datetime.now(timezone.utc).isoformat(),
                    "type": i.decision_type,
                    "severity": sev,
                    "category": "workflow",
                    "message": f"[{i.component_name}] {getattr(i, 'summary', None) or i.rationale}"
                }))
    except Exception as e:
        logger.warning(f"[WS] Lineage history failed, falling back to event_bus: {e}")
        for evt in event_bus.recent(20):
            try:
                # Ensure it has the required fields
                mapped = {
                    "seq": evt.get("seq", int(datetime.now(timezone.utc).timestamp() * 1000)),
                    "timestamp": evt.get("timestamp", datetime.now(timezone.utc).isoformat()),
                    "type": evt.get("type", "EVENT"),
                    "severity": evt.get("severity", "info"),
                    "category": evt.get("category", "workflow"),
                    "message": evt.get("message") or evt.get("rationale") or f"Event: {evt.get('type')}"
                }
                await ws.send_text(json.dumps(mapped, default=str))
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


@app.websocket("/ws/logs")
async def websocket_logs(ws: WebSocket):
    await _authenticated_websocket_stream(ws)


@app.websocket("/ws/events")
async def websocket_events(ws: WebSocket):
    await _authenticated_websocket_stream(ws)


# ── Sistem Endpoint'leri ──────────────────────────────────
@app.get("/health", tags=["Sistem"])
@app.get("/api/v1/health", tags=["Sistem"], include_in_schema=False)
async def health_check():
    from libs.db.session import is_db_available
    from services.orchestration.agency.loader import agency_loader
    from services.observability.memory_governor import memory_governor
    from services.orchestration.agi.cognitive.sovereign_cortex import sovereign_cortex as orchestrator
    from services.orchestration.agi.governance.watchdog import governance_watchdog
    from services.repair.application.heal_engine import heal_engine
    from libs.infra.ws_manager import ws_manager
    from services.orchestration.application.job_queue import job_queue

    async def _with_timeout(coro, timeout_s: float, fallback):
        try:
            return await asyncio.wait_for(coro, timeout=timeout_s)
        except Exception:
            return fallback

    db_ok = await _with_timeout(is_db_available(), 1.5, False)
    db_fallback = await _with_timeout(import_db_degraded(), 0.5, False)
    redis_status = await _with_timeout(
        _get_redis_status(),
        1.0,
        {"available": False, "error": "timeout"},
    )
    repair_summary = await _with_timeout(
        asyncio.to_thread(_get_repair_health_summary),
        1.0,
        {"available": False, "error": "timeout"},
    )
    current_agents = len(orchestrator._agents) if hasattr(orchestrator, "_agents") else 0
    specialists = len(agency_loader.agents)
    mem_usage = memory_governor.get_current_usage_mb()

    return {
        "status": "degraded" if (not db_ok or mem_usage > memory_governor.MAX_MEMORY_MB) else "ok",
        "reason": "memory_limit_exceeded" if mem_usage > memory_governor.MAX_MEMORY_MB else ("db_failed" if not db_ok else None),
        "version": APP_VERSION,
        "v13_stabilized_final": True,
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
        "db": {
            "available": db_ok,
            "error": "Database connection failed" if not db_ok else "",
            "is_fallback": db_fallback,
        },
        "redis": redis_status,
        "queue": {
            "backend": getattr(job_queue, "backend_name", "unknown"),
            "supports_registration": getattr(job_queue, "supports_registration", False),
            "stats": job_queue.stats() if hasattr(job_queue, "stats") else {},
        },
        "repair": repair_summary,
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
    from libs.db.session import is_db_available
    from services.orchestration.agi.cognitive.sovereign_cortex import sovereign_cortex as orchestrator
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
    from services.observability.metrics import metrics
    return metrics.snapshot()


# ── Yardımcılar ───────────────────────────────────────────
async def _get_redis_status() -> dict:
    try:
        from libs.db.session import get_redis_client
        r = await get_redis_client()
        if r:
            await r.ping()
            return {"available": True}
        return {"available": False, "error": "Redis client not initialized"}
    except Exception as e:
        return {"available": False, "error": str(e)}

async def import_db_degraded() -> bool:
    try:
        from libs.db.session import is_db_degraded
        return is_db_degraded()
    except Exception:
        return False

def _get_process_memory() -> str:
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return f"{process.memory_info().rss / 1024 / 1024:.2f} MB"
    except ImportError:
        return "N/A (psutil missing)"


def _get_repair_health_summary() -> dict:
    try:
        from services.repair.repair_orchestrator import get_repair_orchestrator
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


# ── Final Catch-all for SPA ───────────────────────────────
# MUST be the last route to avoid intercepting /health or /api
if _dashboard_static_enabled and os.path.isdir(_active_dash):
    @app.get("/{file_path:path}", include_in_schema=False)
    async def catch_all_static(file_path: str):
        # Skip if it looks like an API call
        if file_path.startswith("api/") or file_path.startswith("ws/"):
            return None # Process via routers

        full_path = os.path.join(_active_dash, file_path)
        if os.path.isfile(full_path):
            return FileResponse(full_path)

        # Fallback to index.html for SPA routing
        index_path = os.path.join(_active_dash, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)

        return None
else:
    def _build_api_only_status_page() -> str:
        dashboard_dev_url = os.getenv("DASHBOARD_DEV_URL", "http://127.0.0.1:3100")
        api_base_url = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api/v1")
        health_url = os.getenv("API_HEALTH_URL", "http://127.0.0.1:8000/health")
        dashboard_health_url = os.getenv("API_DASHBOARD_HEALTH_URL", "http://127.0.0.1:8000/api/v1/health/dashboard")
        ws_url = os.getenv("API_WS_URL", "ws://127.0.0.1:8000/ws/events")

        return f"""<!doctype html>
<html lang="tr">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Sovereign Public API</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #060a12;
      --panel: rgba(17, 24, 39, 0.9);
      --panel-border: rgba(102, 252, 241, 0.16);
      --text: #f3f4f6;
      --muted: #94a3b8;
      --accent: #66fcf1;
      --accent-2: #45a29e;
      --chip: rgba(102, 252, 241, 0.08);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      font-family: Inter, Segoe UI, Arial, sans-serif;
      background:
        radial-gradient(circle at top right, rgba(69,162,158,0.18), transparent 28%),
        linear-gradient(180deg, #08101c 0%, var(--bg) 100%);
      color: var(--text);
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 24px;
    }}
    .shell {{
      width: min(920px, 100%);
      background: var(--panel);
      border: 1px solid var(--panel-border);
      border-radius: 24px;
      padding: 28px;
      box-shadow: 0 20px 50px rgba(0,0,0,0.35);
      backdrop-filter: blur(14px);
    }}
    .eyebrow {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 6px 12px;
      border-radius: 999px;
      background: var(--chip);
      color: var(--accent);
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }}
    h1 {{
      margin: 18px 0 8px;
      font-size: clamp(32px, 5vw, 52px);
      line-height: 1.05;
    }}
    p {{
      margin: 0;
      color: var(--muted);
      font-size: 16px;
      line-height: 1.6;
      max-width: 70ch;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 14px;
      margin-top: 28px;
    }}
    .card {{
      border: 1px solid rgba(255,255,255,0.06);
      border-radius: 16px;
      padding: 16px;
      background: rgba(255,255,255,0.02);
    }}
    .label {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 8px;
    }}
    .value {{
      font-size: 20px;
      font-weight: 700;
      color: var(--text);
      word-break: break-word;
    }}
    .value.ok {{ color: var(--accent); }}
    .links {{
      margin-top: 24px;
      display: grid;
      gap: 10px;
    }}
    a {{
      color: var(--accent);
      text-decoration: none;
    }}
    a:hover {{ color: #8ffdf5; }}
    code {{
      font-family: Consolas, monospace;
      color: #d1d5db;
      font-size: 13px;
    }}
  </style>
</head>
<body>
  <main class="shell">
    <div class="eyebrow">Sovereign Public API</div>
    <h1>8000 ayakta, UI burada değil.</h1>
    <p>
      Bu port şu anda <strong>API ve WebSocket</strong> servisi olarak çalışıyor.
      Geliştirme arayüzü ayrı olarak <a href="{dashboard_dev_url}">{dashboard_dev_url}</a> üstünden sunuluyor.
    </p>

    <section class="grid">
      <div class="card">
        <div class="label">Servis</div>
        <div class="value">workflow_api</div>
      </div>
      <div class="card">
        <div class="label">Durum</div>
        <div class="value ok">healthy</div>
      </div>
      <div class="card">
        <div class="label">UI Modu</div>
        <div class="value">{APP_UI_MODE}</div>
      </div>
      <div class="card">
        <div class="label">Kontrol Paneli</div>
        <div class="value"><a href="{dashboard_dev_url}">3100 UI</a></div>
      </div>
    </section>

    <section class="links">
      <div><code>Health:</code> <a href="{health_url}">{health_url}</a></div>
      <div><code>Dashboard Health:</code> <a href="{dashboard_health_url}">{dashboard_health_url}</a></div>
      <div><code>API Base:</code> <a href="{api_base_url}">{api_base_url}</a></div>
      <div><code>WebSocket:</code> <code>{ws_url}</code></div>
    </section>
  </main>
</body>
</html>"""

    @app.get("/", include_in_schema=False)
    async def api_only_root():
        return HTMLResponse(_build_api_only_status_page())
