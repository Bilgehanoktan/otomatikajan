"""
libs/infra/middleware.py — Phase 13.04
Standardized middleware for all Sovereign AGI API services.
"""
from __future__ import annotations

import time
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from services.observability.logging import get_logger

logger = get_logger("infra.middleware")

def configure_middleware(app: FastAPI):
    """
    Apply standard middleware stack to a FastAPI application.
    """
    # 1. CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Production should restrict this
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. Performance & Request Logging Middleware
    app.add_middleware(RequestTimeLoggingMiddleware)
    
    # 3. OTel Middleware (Lazy optional)
    try:
        from libs.observability.middleware import get_otel_middleware
        otel_mw = get_otel_middleware()
        if otel_mw:
            app.add_middleware(otel_mw)
            logger.info("[MIDDLEWARE] OTel Tracing enabled.")
    except Exception as e:
        logger.warning(f"[MIDDLEWARE] OTel could not be initialized: {e}")

class RequestTimeLoggingMiddleware(BaseHTTPMiddleware):
    """Logs request duration and basic metadata."""
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        
        # SRE Robustness: Trace ID propagation if OTel fails
        request_id = request.headers.get("X-Request-ID", "unknown")
        
        response = await call_next(request)
        
        process_time = (time.perf_counter() - start_time) * 1000
        logger.info(
            f"{request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"ID: {request_id} - "
            f"Duration: {process_time:.2f}ms"
        )
        
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
        return response
