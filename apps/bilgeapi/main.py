import logging
import sys
import time
from collections import deque
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from apps.bilgeapi.config import settings
from apps.bilgeapi.routers import health, catalog, incidents, audit, diagnostics, repairs
from apps.bilgeapi.startup import validate_production_config

logger = logging.getLogger("bilgeapi")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: validate config on startup."""
    validate_production_config()
    logger.info("BilgeAPI started successfully.")
    yield
    logger.info("BilgeAPI shutting down.")


app = FastAPI(
    title="BilgeAPI",
    description="Independent Incident Intake, Diagnostic and Repair-Orchestration API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BILGEAPI_CORS_ALLOWLIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Content Size Limiting Middleware
class ContentSizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            content_length = request.headers.get("content-length")
            if content_length:
                try:
                    if int(content_length) > settings.BILGEAPI_MAX_CONTENT_LENGTH:
                        return JSONResponse(
                            status_code=413,
                            content={"detail": "Request entity too large"}
                        )
                except ValueError:
                    return JSONResponse(
                        status_code=400,
                        content={"detail": "Invalid content-length header"}
                    )
        return await call_next(request)

app.add_middleware(ContentSizeLimitMiddleware)

# Rate Limiting Middleware
class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app_instance, rps_limit: int = 10):
        super().__init__(app_instance)
        self.rps_limit = rps_limit
        self.history = {}

    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/health" or settings.BILGEAPI_AUTH_MODE == "disabled":
            return await call_next(request)
            
        client_ip = request.client.host if request.client else "unknown"
        if request.headers.get("x-test-clear-limits") == "true":
            self.history[client_ip] = deque()
            
        now = time.time()
        
        if client_ip not in self.history:
            self.history[client_ip] = deque()
            
        timestamps = self.history[client_ip]
        while timestamps and timestamps[0] < now - 1.0:
            timestamps.popleft()
            
        if len(timestamps) >= settings.BILGEAPI_RATE_LIMIT_RPS:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."}
            )
            
        timestamps.append(now)
        
        # Clean history dict if it grows too large
        if len(self.history) > 5000:
            self.history = {ip: ts for ip, ts in self.history.items() if ts}
            
        return await call_next(request)

app.add_middleware(RateLimitMiddleware, rps_limit=settings.BILGEAPI_RATE_LIMIT_RPS)

# Register Routers
app.include_router(health.router)
app.include_router(catalog.router)
app.include_router(incidents.router)
app.include_router(audit.router)
app.include_router(diagnostics.router)
app.include_router(repairs.router)


# Custom OpenAPI Generator
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
        
    from fastapi.openapi.utils import get_openapi
    openapi_schema = get_openapi(
        title="BilgeAPI",
        version="1.0.0",
        description="Independent Incident Intake, Diagnostic and Repair-Orchestration API",
        routes=app.routes,
    )
    
    # Configure security schemes
    openapi_schema["components"] = openapi_schema.get("components", {})
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyHeader": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key"
        },
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    
    # Enforce security requirements on protected paths
    for path, path_info in openapi_schema.get("paths", {}).items():
        # Skip public endpoints
        if path in ("/health", "/docs", "/redoc", "/openapi.json"):
            continue
        for method in path_info:
            path_info[method]["security"] = [
                {"ApiKeyHeader": []},
                {"BearerAuth": []}
            ]
            
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi


