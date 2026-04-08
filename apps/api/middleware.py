"""
startup/middleware.py — Middleware yapılandırması.

CORS, request tracing ve rate limiting middleware'leri burada kayıt altına alınır.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import ALLOWED_ORIGINS, ALLOWED_METHODS, ALLOWED_HEADERS
from packages.observability.logging import RequestTracingMiddleware
from apps.api.support.rate_limiter import RateLimitHeaderMiddleware


def configure_middleware(app: FastAPI) -> None:
    """Uygulama middleware'lerini kaydet."""
    app.add_middleware(RateLimitHeaderMiddleware)
    app.add_middleware(RequestTracingMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS if "*" not in ALLOWED_ORIGINS else ["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=ALLOWED_METHODS,
        allow_headers=ALLOWED_HEADERS,
        expose_headers=["X-Trace-ID", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
    )
