"""
apps/bilgeapi/routers/metrics.py — Phase 10
Prometheus-compatible /metrics endpoint for BilgeAPI.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import PlainTextResponse
from apps.bilgeapi.config import settings

logger = logging.getLogger("bilgeapi.metrics")

router = APIRouter()


def _metrics_guard(request: Request):
    """
    In production, /metrics requires admin auth unless BILGEAPI_METRICS_PUBLIC=true.
    In dev/test, /metrics is always public.
    """
    if settings.APP_ENV == "production" and not settings.BILGEAPI_METRICS_PUBLIC:
        # Check for API key with admin role
        from apps.bilgeapi.auth import parse_static_keys
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            raise HTTPException(status_code=401, detail="Metrics endpoint requires authentication in production")
        key_roles = parse_static_keys()
        role = key_roles.get(api_key)
        if role not in ("ADMIN", "SOVEREIGN_PRIME"):
            raise HTTPException(status_code=403, detail="Metrics endpoint requires admin privileges")


@router.get("/metrics", tags=["Observability"], response_class=PlainTextResponse)
async def prometheus_metrics(request: Request):
    """Expose Prometheus-format metrics for scraping."""
    _metrics_guard(request)
    try:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        return PlainTextResponse(
            content=generate_latest().decode("utf-8"),
            media_type=CONTENT_TYPE_LATEST,
        )
    except ImportError:
        logger.warning("prometheus_client not installed, /metrics returning empty")
        return PlainTextResponse(
            content="# prometheus_client not available\n",
            media_type="text/plain",
        )
