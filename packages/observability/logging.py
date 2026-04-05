"""
Yapılandırılmış Loglama — Faz 2
• Her log satırı JSON — production'da kolayca parse edilir
• Request ID takibi (trace)
• Seviye bazlı filtreleme
• DB'ye otomatik önemli olayları yaz (async)
• Standart Python logging entegrasyonu
"""

import json
import logging
import os
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

# Her request için benzersiz trace ID
_trace_id: ContextVar[str] = ContextVar("trace_id", default="")

# Config modülünden oku (standart kaynak)
try:
    from config import APP_ENV, LOG_LEVEL
except ImportError:
    APP_ENV   = os.getenv("APP_ENV", "development")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG" if APP_ENV == "development" else "INFO")


def get_trace_id() -> str:
    return _trace_id.get() or "no-trace"

def set_trace_id(tid: str = "") -> str:
    tid = tid or str(uuid.uuid4())[:8]
    _trace_id.set(tid)
    return tid


# ════════════════════════════════════════════════════════
# JSON Log Formatter
# ════════════════════════════════════════════════════════
class JSONFormatter(logging.Formatter):
    SKIP_FIELDS = {"msg", "args", "exc_info", "exc_text", "stack_info",
                   "levelno", "pathname", "filename", "module",
                   "created", "msecs", "relativeCreated", "thread",
                   "threadName", "processName", "process"}

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts":       datetime.now(timezone.utc).isoformat(),
            "level":    record.levelname,
            "logger":   record.name,
            "trace_id": get_trace_id(),
            "message":  record.getMessage(),
        }

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        # Extra alanlar
        for k, v in record.__dict__.items():
            if k not in self.SKIP_FIELDS and not k.startswith("_"):
                try:
                    json.dumps(v)   # serileştirilebilir mi?
                    payload[k] = v
                except (TypeError, ValueError):
                    payload[k] = str(v)

        return json.dumps(payload, ensure_ascii=False)


# ════════════════════════════════════════════════════════
# DB'ye Önemli Olayları Yazan Handler
# ════════════════════════════════════════════════════════
class DBLogHandler(logging.Handler):
    """WARNING+ seviyedeki logları domain_event_logs tablosuna yazar."""

    def emit(self, record: logging.LogRecord):
        if record.levelno < logging.WARNING:
            return
        
        # Don't log if we are already inside a log writing operation (prevent recursion)
        if getattr(record, "_is_logging_db", False):
            return

        try:
            import asyncio
            from db.session import AsyncSessionLocal
            from db.repository import EventLogRepository

            async def _write():
                try:
                    # 1. DB Log (Relational)
                    async with AsyncSessionLocal() as db:
                        from db.repository import EventLogRepository
                        await EventLogRepository.write(
                            db,
                            event_type=f"log.{record.levelname.lower()}",
                            agent_id=getattr(record, "agent_id", "system"),
                            severity="warning" if record.levelno == logging.WARNING else "critical",
                            phase=getattr(record, "phase", "log"),
                            message=record.getMessage()[:2000],
                            payload={"logger": record.name, "trace_id": get_trace_id()},
                        )
                        await db.commit()
                    
                    # 2. Vector Log (Faz 12.2: Log Aggregation to RAG)
                    try:
                        from memory.watchdog import watchdog
                        agent_id = getattr(record, "agent_id", "system")
                        severity = "warning" if record.levelno == logging.WARNING else "critical"
                        phase = getattr(record, "phase", "log")
                        await watchdog.log_event(agent_id, severity, phase, record.getMessage())
                    except Exception:
                        pass
                except Exception:
                    pass

            try:
                loop = asyncio.get_running_loop()
                if loop.is_running():
                    # Set a flag to prevent recursive logging if the DB write itself fails and logs
                    record._is_logging_db = True
                    asyncio.create_task(_write())
            except RuntimeError:
                # No running loop, run in a one-off way
                # (Can be slow but this is for WARNING+ errors in sync context)
                asyncio.run(_write())
        except Exception:
            pass  # Log handler asla exception fırlatmaz


# ════════════════════════════════════════════════════════
# Logger Factory
# ════════════════════════════════════════════════════════
def get_logger(name: str, force_db: bool = False) -> logging.Logger:
    """
    Logger instance döndürür.
    force_db=True verilirse her durumda (dev/prod fark etmeksizin) DBLogHandler eklenir.
    """
    logger = logging.getLogger(name)
    
    # ── KRITIK: Her durumda propagate kapatilmali (Faz 12 Fix) ───
    logger.propagate = False

    if logger.handlers:
        # DB Handler zaten var mı kontrol et (force_db durumunda mükerrer eklememek için)
        if force_db:
            has_db = any(isinstance(h, DBLogHandler) for h in logger.handlers)
            if not has_db:
                logger.addHandler(DBLogHandler())
        return logger

    logger.setLevel(getattr(logging, LOG_LEVEL, logging.DEBUG))

    # Stdout — JSON (prod) veya insan okunabilir (dev)
    handler = logging.StreamHandler(sys.stdout)
    if APP_ENV == "production":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s  %(levelname)-8s  [%(name)s]  %(message)s",
                datefmt="%H:%M:%S",
            )
        )
    logger.addHandler(handler)

    # DB handler ekle (Production'da otomatik, veya zorunluysa her zaman)
    if APP_ENV == "production" or force_db:
        logger.addHandler(DBLogHandler())

    return logger


# ── Root logger konfigürasyonu ─────────────────────────
def configure_logging(level: int = logging.INFO):
    """
    Sistemi genel log ayarlarına çeker.
    main.py lifespan'dan veya Celery worker startup'ından çağrılır.
    """
    root = logging.getLogger()
    
    # Seviye ayarı (3. parti kütüphaneleri susturmak için varsayılan WARNING)
    root.setLevel(logging.WARNING)

    # Kendi kritik modüllerimiz için logger'ları ilklendir
    modules = ("main", "core", "api", "auth", "db", "heal", "llm", "tasks", "webhooks", "deerflow_bridge")
    for name in modules:
        get_logger(name)

    # ── KRITIK: Tüm log hiyerarşisini tara ve duplikasyonu engelle ──
    for name in logging.root.manager.loggerDict:
        l = logging.getLogger(name)
        if hasattr(l, "handlers") and l.handlers:
            l.propagate = False

    # uvicorn'u susturma — access loglarını görmek iyidir
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)


# ── FastAPI Request Tracing Middleware ────────────────────
try:
    from starlette.middleware.base import BaseHTTPMiddleware as _MBase

    class RequestTracingMiddleware(_MBase):
        async def dispatch(self, request, call_next):
            import time
            tid = request.headers.get("X-Trace-ID") or set_trace_id()
            set_trace_id(tid)
            t0 = time.time()
            response = await call_next(request)
            response.headers["X-Trace-ID"] = tid
            
            # ── Degrade Mode Visibility (P1-05) ───────────────────
            try:
                from db.session import is_db_available
                # core.heal_engine import'i circular import riski için içeride
                from packages.healing.application.heal_engine import heal_engine
                db_ok = await is_db_available()
                h_score = heal_engine.system_health_score()
                
                if not db_ok or h_score < 0.7:
                    response.headers["X-System-Status"] = "degraded"
                    if not db_ok:
                        response.headers["X-System-Reason"] = "database_unavailable"
                    elif h_score < 0.7:
                        response.headers["X-System-Reason"] = "agent_unhealthiness"
                else:
                    response.headers["X-System-Status"] = "ok"
            except Exception:
                pass
            # ──────────────────────────────────────────────────────
            elapsed_ms = (time.time() - t0) * 1000

            # ApiMetric'i DB'ye kaydet (non-blocking)
            path = str(request.url.path)
            skip = ("/health", "/metrics", "/static", "/ws", "/favicon")
            # Sampling: hata varsa her zaman yaz, normal trafikte %20
            import random as _random
            is_error = response.status_code >= 400
            should_sample = is_error or _random.random() < 0.20
            if not any(path.startswith(s) for s in skip) and should_sample:
                try:
                    import asyncio
                    from db.session import AsyncSessionLocal
                    from db.repository import ApiMetricRepository
                    error_type = "" if not is_error else f"HTTP_{response.status_code}"
                    async def _write():
                        try:
                            async with AsyncSessionLocal() as db:
                                await ApiMetricRepository.write(
                                    db,
                                    endpoint=path,
                                    method=request.method,
                                    status_code=response.status_code,
                                    response_ms=round(elapsed_ms, 1),
                                    trace_id=tid,
                                    ip_address=request.client.host if request.client else "",
                                    error_type=error_type,
                                )
                                await db.commit()
                        except Exception:
                            pass
                    asyncio.create_task(_write())
                except Exception:
                    pass
            return response
except ImportError:
    class RequestTracingMiddleware:  # type: ignore
        pass
