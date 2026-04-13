"""
libs/observability/middleware.py — Phase 13.04
FastAPI/Starlette middleware that creates an OTel span per HTTP request.

Features:
  - Root span per request with method/path/status attributes
  - W3C traceparent propagation from incoming headers
  - X-Trace-ID response header populated with OTel trace id
  - Celery task header injection helper (for distributed tracing)
"""
from __future__ import annotations

import time
from typing import Callable

try:
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import Response
    _HAS_STARLETTE = True
except ImportError:
    _HAS_STARLETTE = False

from libs.observability.tracer import (
    _OTEL_AVAILABLE, inject_headers, extract_context, correlation_id
)

if _OTEL_AVAILABLE:
    from opentelemetry import trace as _ot_trace
    from opentelemetry.semconv.trace import SpanAttributes


def get_otel_middleware():
    """
    Returns the OTel tracing middleware class.
    Falls back to a transparent pass-through if OTel or Starlette is unavailable.
    """
    if not _HAS_STARLETTE:
        return None

    if not _OTEL_AVAILABLE:
        class PassThrough(BaseHTTPMiddleware):
            async def dispatch(self, request: Request, call_next: Callable) -> Response:
                return await call_next(request)
        return PassThrough

    class OTelTracingMiddleware(BaseHTTPMiddleware):
        """
        Creates an OTel server span for every HTTP request.
        Propagates W3C trace context from inbound headers.
        """

        async def dispatch(self, request: Request, call_next: Callable) -> Response:
            # Extract upstream trace context (e.g. from API gateway or Celery)
            carrier = dict(request.headers)
            ctx = extract_context(carrier)

            tracer = _ot_trace.get_tracer("sovereign.http")
            route_path = getattr(request, "scope", {}).get("path", request.url.path)
            span_name  = f"{request.method} {route_path}"

            with tracer.start_as_current_span(
                span_name,
                context=ctx,
                kind=_ot_trace.SpanKind.SERVER,
            ) as s:
                if s.is_recording():
                    s.set_attribute(SpanAttributes.HTTP_METHOD,      request.method)
                    s.set_attribute(SpanAttributes.HTTP_URL,         str(request.url))
                    s.set_attribute(SpanAttributes.HTTP_TARGET,      request.url.path)
                    s.set_attribute(SpanAttributes.HTTP_HOST,        request.url.netloc)
                    s.set_attribute(SpanAttributes.HTTP_SCHEME,      request.url.scheme)
                    s.set_attribute("http.user_agent",               request.headers.get("user-agent", ""))
                    if request.client:
                        s.set_attribute(SpanAttributes.NET_PEER_IP, request.client.host)

                t0 = time.perf_counter()
                response: Response = await call_next(request)
                duration_ms = (time.perf_counter() - t0) * 1000

                if s.is_recording():
                    s.set_attribute(SpanAttributes.HTTP_STATUS_CODE, response.status_code)
                    s.set_attribute("http.duration_ms", round(duration_ms, 2))

                    if response.status_code >= 500:
                        s.set_status(
                            _ot_trace.Status(
                                _ot_trace.StatusCode.ERROR,
                                f"HTTP {response.status_code}"
                            )
                        )

                # Add OTel trace ID to response header for dashboard correlation
                corr = correlation_id()
                if corr != "no-otel":
                    response.headers["X-OTel-Trace-ID"] = corr

                return response

    return OTelTracingMiddleware


# ── Celery task header injection ──────────────────────────────────────────────

def inject_celery_headers(headers: dict | None = None) -> dict:
    """
    Inject current OTel trace context into Celery task headers.
    Call this before `task.apply_async(headers=inject_celery_headers())`.
    """
    carrier: dict = headers or {}
    if _OTEL_AVAILABLE:
        inject_headers(carrier)
    return carrier


def extract_celery_context(headers: dict | None = None):
    """
    Extract OTel trace context from Celery task headers on the worker side.
    Call this at the start of a Celery task to restore parent trace context.
    """
    if not _OTEL_AVAILABLE or not headers:
        return None
    return extract_context(headers)
