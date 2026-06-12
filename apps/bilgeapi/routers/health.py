"""
apps/bilgeapi/routers/health.py — Phase 10
Public /health (minimal) and admin-only /v1/ops/health (detailed) endpoints.
"""
import os
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request
from apps.bilgeapi.config import settings
from apps.bilgeapi.auth import require_permission

logger = logging.getLogger("bilgeapi.health")

router = APIRouter()


@router.get("/health", tags=["Health"])
async def health_check(request: Request):
    """Public health check — returns minimal status for load balancers and uptime monitors."""
    skill_registry_status = getattr(request.app.state, "skill_registry_status", "UNKNOWN")
    overall_status = "ok" if skill_registry_status == "HEALTHY" else "degraded"
    return {
        "status": overall_status,
        "service": "bilgeapi",
        "version": settings.BILGEAPI_VERSION,
        "auth_mode": settings.BILGEAPI_AUTH_MODE,
        "skill_registry": skill_registry_status,
    }


@router.get("/v1/ops/health", tags=["Observability"])
async def detailed_health(request: Request, identity: dict = Depends(require_permission("bilgeapi.admin"))):
    """
    Admin-only detailed health check.
    Exposes memory usage, DB connection pool stats, OTel readiness,
    and background task counts.
    """
    # ── Memory ──
    memory_info = _get_memory_info()

    # ── DB Pool ──
    db_info = _get_db_pool_info()

    # ── OTel ──
    otel_info = _get_otel_info()

    # ── Background Tasks ──
    bg_info = _get_background_task_info()

    # ── Skill Registry ──
    skill_registry_status = getattr(request.app.state, "skill_registry_status", "UNKNOWN")
    overall_status = "ok" if skill_registry_status == "HEALTHY" else "degraded"

    return {
        "status": overall_status,
        "service": "bilgeapi",
        "version": settings.BILGEAPI_VERSION,
        "auth_mode": settings.BILGEAPI_AUTH_MODE,
        "environment": settings.APP_ENV,
        "memory": memory_info,
        "db": db_info,
        "otel": otel_info,
        "background_tasks": bg_info,
        "skill_registry": skill_registry_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _get_memory_info() -> dict:
    """Get current process RSS memory usage."""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        rss_mb = process.memory_info().rss / (1024 * 1024)
        return {
            "rss_mb": round(rss_mb, 2),
            "status": "warning" if rss_mb > 512 else "healthy",
        }
    except ImportError:
        return {"rss_mb": None, "status": "unknown", "error": "psutil not installed"}
    except Exception as e:
        return {"rss_mb": None, "status": "error", "error": str(e)}


def _get_db_pool_info() -> dict:
    """Get SQLAlchemy engine connection pool statistics."""
    try:
        import libs.db.session as db_session

        engine = getattr(db_session, "_engine", None)
        if engine is None:
            return {"status": "not_initialized"}

        pool = engine.pool
        return {
            "pool_size": getattr(pool, "size", lambda: None)()
            if callable(getattr(pool, "size", None))
            else getattr(pool, "_pool", {}).maxsize if hasattr(getattr(pool, "_pool", None), "maxsize") else None,
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "status": "healthy",
        }
    except Exception as e:
        return {"status": "unavailable", "error": str(e)}


def _get_otel_info() -> dict:
    """Report OpenTelemetry availability and configuration."""
    try:
        from libs.observability.tracer import (
            _OTEL_AVAILABLE, OTEL_ENABLED, OTEL_ENDPOINT, SERVICE_NAME
        )
        return {
            "enabled": OTEL_ENABLED,
            "available": _OTEL_AVAILABLE,
            "endpoint": OTEL_ENDPOINT if OTEL_ENABLED else None,
            "service_name": SERVICE_NAME,
        }
    except ImportError:
        return {"enabled": False, "available": False, "error": "libs.observability.tracer not importable"}


def _get_background_task_info() -> dict:
    """Report BilgeAPI-managed background task counts."""
    try:
        from apps.bilgeapi.services.webhook import background_tasks
        pending = len([t for t in background_tasks if not t.done()])
        total = len(background_tasks)
        return {"pending": pending, "total_tracked": total}
    except (ImportError, AttributeError):
        return {"pending": 0, "total_tracked": 0}
