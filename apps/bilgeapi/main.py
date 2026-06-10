import asyncio
import logging
import re
import sys
import time
import uuid
from collections import deque
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from apps.bilgeapi.config import settings
from apps.bilgeapi.routers import health, catalog, incidents, audit, diagnostics, repairs, release, adapters, admin_api_keys, improvements, review_ledger, system_watchdog
from apps.bilgeapi.routers import metrics as metrics_router
from apps.bilgeapi.startup import validate_production_config

logger = logging.getLogger("bilgeapi")

REDIS_FALLBACK_ACTIVE = False

# ── Prometheus Counters (module-level, lazy-safe) ─────────────────────────────
try:
    from prometheus_client import Counter, Histogram, Gauge
    REQUEST_COUNT = Counter(
        "bilgeapi_http_requests_total",
        "Total HTTP requests",
        ["method", "path", "status"],
    )
    REQUEST_DURATION = Histogram(
        "bilgeapi_http_request_duration_seconds",
        "HTTP request latency in seconds",
        ["method", "path"],
        buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    )
    WEBHOOK_DELIVERIES = Counter(
        "bilgeapi_webhook_deliveries_total",
        "Total webhook deliveries dispatched",
    )
    WEBHOOK_DEAD_LETTERS = Counter(
        "bilgeapi_webhook_dead_letters_total",
        "Total webhook deliveries moved to dead-letter",
    )
    REPAIR_REQUESTS = Counter(
        "bilgeapi_repair_requests_total",
        "Total repair requests created",
    )
    RELEASE_GATE_SCORE = Gauge(
        "bilgeapi_release_gate_score",
        "Latest release gate score",
    )
    BACKGROUND_TASKS_PENDING = Gauge(
        "bilgeapi_background_tasks_pending",
        "Number of pending background dispatch tasks",
    )
    REDIS_FALLBACK_COUNT = Counter(
        "bilgeapi_redis_fallback_total",
        "Total number of Redis connection failures forcing in-memory rate limit fallback",
    )
    TENANT_REQUESTS = Counter(
        "bilgeapi_tenant_requests_total",
        "Total requests processed per tenant",
        ["tenant_id"],
    )
    _PROMETHEUS_AVAILABLE = True
except ImportError:
    class _FallbackRegistry:
        def __init__(self):
            self.samples = {}
            self.types = {}

        def register(self, name: str, metric_type: str) -> None:
            self.types.setdefault(name, metric_type)

        def add(self, name: str, labels: dict, amount: float) -> None:
            key = (name, tuple(sorted(labels.items())))
            self.samples[key] = self.samples.get(key, 0.0) + amount

        def set(self, name: str, labels: dict, value: float) -> None:
            self.samples[(name, tuple(sorted(labels.items())))] = float(value)

        def get_sample_value(self, name: str, labels: dict | None = None):
            label_items = tuple(sorted((labels or {}).items()))
            return self.samples.get((name, label_items))

        def render(self) -> bytes:
            lines = []
            for name, metric_type in self.types.items():
                lines.append(f"# HELP {name} Fallback metric for {name}")
                lines.append(f"# TYPE {name} {metric_type}")
                matching = [(labels, value) for (sample_name, labels), value in self.samples.items() if sample_name == name]
                if not matching:
                    matching = [(tuple(), 0.0)]
                for labels, value in matching:
                    if labels:
                        label_text = ",".join(f'{k}="{v}"' for k, v in labels)
                        lines.append(f"{name}{{{label_text}}} {value}")
                    else:
                        lines.append(f"{name} {value}")
            return ("\n".join(lines) + "\n").encode("utf-8")

    class _FallbackMetricChild:
        def __init__(self, registry: _FallbackRegistry, name: str, labels: dict):
            self.registry = registry
            self.name = name
            self.labels_map = labels

        def inc(self, amount: float = 1.0) -> None:
            self.registry.add(self.name, self.labels_map, amount)

        def observe(self, amount: float) -> None:
            self.registry.add(self.name, self.labels_map, amount)

        def set(self, value: float) -> None:
            self.registry.set(self.name, self.labels_map, value)

    class _FallbackMetric:
        def __init__(self, name: str, _description: str, labelnames=None, metric_type: str = "gauge", **_kwargs):
            self.name = name
            self.labelnames = list(labelnames or [])
            self.registry = _FALLBACK_REGISTRY
            self.registry.register(name, metric_type)

        def labels(self, *labelvalues, **labelkwargs):
            labels = dict(labelkwargs)
            for index, value in enumerate(labelvalues):
                if index < len(self.labelnames):
                    labels[self.labelnames[index]] = value
            return _FallbackMetricChild(self.registry, self.name, labels)

        def inc(self, amount: float = 1.0) -> None:
            self.registry.add(self.name, {}, amount)

        def observe(self, amount: float) -> None:
            self.registry.add(self.name, {}, amount)

        def set(self, value: float) -> None:
            self.registry.set(self.name, {}, value)

    _FALLBACK_REGISTRY = _FallbackRegistry()

    def _fallback_generate_latest(registry=None):
        return (registry or _FALLBACK_REGISTRY).render()

    import types
    _fallback_prometheus = types.ModuleType("prometheus_client")
    _fallback_prometheus.REGISTRY = _FALLBACK_REGISTRY
    _fallback_prometheus.CONTENT_TYPE_LATEST = "text/plain; version=0.0.4"
    _fallback_prometheus.generate_latest = _fallback_generate_latest
    _fallback_prometheus.Counter = lambda name, description, labelnames=None, **kwargs: _FallbackMetric(
        name, description, labelnames, metric_type="counter", **kwargs
    )
    _fallback_prometheus.Histogram = lambda name, description, labelnames=None, **kwargs: _FallbackMetric(
        name, description, labelnames, metric_type="histogram", **kwargs
    )
    _fallback_prometheus.Gauge = lambda name, description, labelnames=None, **kwargs: _FallbackMetric(
        name, description, labelnames, metric_type="gauge", **kwargs
    )
    sys.modules.setdefault("prometheus_client", _fallback_prometheus)

    Counter = _fallback_prometheus.Counter
    Histogram = _fallback_prometheus.Histogram
    Gauge = _fallback_prometheus.Gauge
    REQUEST_COUNT = Counter(
        "bilgeapi_http_requests_total",
        "Total HTTP requests",
        ["method", "path", "status"],
    )
    REQUEST_DURATION = Histogram(
        "bilgeapi_http_request_duration_seconds",
        "HTTP request latency in seconds",
        ["method", "path"],
    )
    WEBHOOK_DELIVERIES = Counter("bilgeapi_webhook_deliveries_total", "Total webhook deliveries dispatched")
    WEBHOOK_DEAD_LETTERS = Counter("bilgeapi_webhook_dead_letters_total", "Total webhook deliveries moved to dead-letter")
    REPAIR_REQUESTS = Counter("bilgeapi_repair_requests_total", "Total repair requests created")
    RELEASE_GATE_SCORE = Gauge("bilgeapi_release_gate_score", "Latest release gate score")
    BACKGROUND_TASKS_PENDING = Gauge("bilgeapi_background_tasks_pending", "Number of pending background dispatch tasks")
    REDIS_FALLBACK_COUNT = Counter(
        "bilgeapi_redis_fallback_total",
        "Total number of Redis connection failures forcing in-memory rate limit fallback",
    )
    TENANT_REQUESTS = Counter(
        "bilgeapi_tenant_requests_total",
        "Total requests processed per tenant",
        ["tenant_id"],
    )
    _PROMETHEUS_AVAILABLE = True

# ── Path sanitization for Prometheus labels ───────────────────────────────────
_UUID_RE = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)
_ID_SEGMENT_RE = re.compile(r"/[0-9a-fA-F]{8,}(?=[/]|$)")


def sanitize_path(path: str) -> str:
    """Replace dynamic UUIDs and IDs in paths with placeholders for low-cardinality labels."""
    path = _UUID_RE.sub("{uuid}", path)
    path = _ID_SEGMENT_RE.sub("/{id}", path)
    return path


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: validate config on startup, drain tasks on shutdown."""
    # Startup
    try:
        from services.observability.logging import configure_logging
        configure_logging()
        logger.info("[LIFECYCLE] Logging configured via services.observability.logging")
    except ImportError:
        logger.warning("[LIFECYCLE] services.observability.logging not available, using defaults")

    validate_production_config()
    
    if settings.BILGEAPI_DURABLE_QUEUE_ENABLED:
        from libs.queue_abstractions.job_queue import job_queue
        
        async def _durable_webhook_handler(
            delivery_id: str,
            repair_request_id: str,
            webhook_url: str,
            payload: dict,
            attempt: int,
            adapter: str,
            dry_run: bool,
            **kwargs
        ):
            from apps.bilgeapi.services.webhook import run_webhook_dispatch_job
            await run_webhook_dispatch_job(
                delivery_id=delivery_id,
                repair_request_id=repair_request_id,
                webhook_url=webhook_url,
                payload=payload,
                attempt=attempt,
                adapter=adapter,
                dry_run=dry_run
            )
            
        job_queue.register("bilgeapi_webhook_delivery", _durable_webhook_handler)
        asyncio.create_task(job_queue.start(num_workers=2))
        logger.info("[STARTUP] BilgeAPI JobQueue workers started.")
        
    logger.info("BilgeAPI started successfully.")
    yield

    # Shutdown — drain BilgeAPI-managed background tasks
    logger.info("BilgeAPI shutting down — draining background tasks...")
    if settings.BILGEAPI_DURABLE_QUEUE_ENABLED:
        try:
            from libs.queue_abstractions.job_queue import job_queue
            logger.info("Stopping BilgeAPI local JobQueue workers...")
            await job_queue.stop()
        except Exception as e:
            logger.warning(f"Error stopping JobQueue: {e}")
            
    try:
        from apps.bilgeapi.services.webhook import background_tasks as webhook_background_tasks
        from apps.bilgeapi.services.diagnostic import background_tasks as diagnostic_background_tasks
        managed_background_tasks = set(webhook_background_tasks) | set(diagnostic_background_tasks)
        pending = [t for t in managed_background_tasks if not t.done()]
        if pending:
            timeout = settings.BILGEAPI_SHUTDOWN_TIMEOUT_S
            logger.info(f"Waiting for {len(pending)} pending background tasks (timeout={timeout}s)...")
            done, not_done = await asyncio.wait(pending, timeout=timeout)
            if not_done:
                logger.warning(f"{len(not_done)} background tasks did not complete within timeout — cancelling")
                for t in not_done:
                    t.cancel()
        else:
            logger.info("No pending background tasks to drain.")
    except (ImportError, AttributeError):
        pass
    logger.info("BilgeAPI shutdown complete.")


app = FastAPI(
    title="BilgeAPI",
    description="Independent Incident Intake, Diagnostic and Repair-Orchestration API",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS Middleware ───────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BILGEAPI_CORS_ALLOWLIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Content Size Limiting Middleware ──────────────────────────────────────────
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


# ── X-Correlation-ID Middleware ───────────────────────────────────────────────
class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """
    Preserves inbound X-Correlation-ID header or generates a new UUID.
    Sets the correlation ID on the response header and injects it into
    the logging context for log correlation.
    """
    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())

        # Inject into logging context
        try:
            from services.observability.logging import set_trace_id
            set_trace_id(correlation_id[:8])
        except ImportError:
            pass

        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response

app.add_middleware(CorrelationIDMiddleware)


# ── Security Headers Middleware ───────────────────────────────────────────────
# Paths that skip FULL CSP (docs require inline scripts/styles for Swagger UI)
_DOCS_BYPASS_PATHS = {"/docs", "/redoc", "/openapi.json"}

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        path = request.url.path

        if path in _DOCS_BYPASS_PATHS:
            # Docs paths — only skip CSP; keep basic security headers
            return response

        # All other paths including /health and /metrics get basic security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # /health and /metrics skip strict CSP but keep nosniff
        if path not in ("/health", "/metrics", "/v1/ops/health"):
            response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if settings.APP_ENV == "production" and path not in ("/health", "/metrics"):
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response

app.add_middleware(SecurityHeadersMiddleware)


# ── Prometheus Metrics Middleware ─────────────────────────────────────────────
if _PROMETHEUS_AVAILABLE:
    class PrometheusMetricsMiddleware(BaseHTTPMiddleware):
        """Counts HTTP requests and measures latency with sanitized path labels."""

        _SKIP_PATHS = {"/health", "/metrics", "/docs", "/redoc", "/openapi.json"}

        async def dispatch(self, request: Request, call_next):
            if request.url.path in self._SKIP_PATHS:
                return await call_next(request)

            method = request.method
            path_label = sanitize_path(request.url.path)

            start = time.perf_counter()
            response = await call_next(request)
            duration = time.perf_counter() - start

            REQUEST_COUNT.labels(method=method, path=path_label, status=response.status_code).inc()
            REQUEST_DURATION.labels(method=method, path=path_label).observe(duration)

            # Update background tasks gauge
            try:
                from apps.bilgeapi.services.webhook import background_tasks
                BACKGROUND_TASKS_PENDING.set(len([t for t in background_tasks if not t.done()]))
            except (ImportError, AttributeError):
                pass

            return response

    app.add_middleware(PrometheusMetricsMiddleware)


# ── OTel Tracing Middleware ───────────────────────────────────────────────────
try:
    from libs.observability.middleware import get_otel_middleware
    _OTelMW = get_otel_middleware()
    if _OTelMW is not None:
        app.add_middleware(_OTelMW)
        logger.info("[OTEL] Tracing middleware registered for BilgeAPI")
except Exception as _otel_err:
    logger.warning(f"[OTEL] Middleware skipped: {_otel_err}")


# ── Exception Handlers ────────────────────────────────────────────────────────
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=getattr(exc, "headers", None)
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled internal server error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"}
    )


# ── Rate Limiting Middleware ──────────────────────────────────────────────────
class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app_instance, rps_limit: int = 10):
        super().__init__(app_instance)
        self.rps_limit = rps_limit
        self.history = {}
        self.redis_client = None
        self._redis_fallback_logged = False

    _BYPASS_PATHS = {"/health", "/metrics"}

    def _get_redis_client(self):
        if not settings.BILGEAPI_REDIS_URL:
            return None
        if self.redis_client is None:
            try:
                import redis
                # Parse host/port/db from BILGEAPI_REDIS_URL or use from_url
                self.redis_client = redis.Redis.from_url(
                    settings.BILGEAPI_REDIS_URL,
                    socket_connect_timeout=1.0,
                    socket_timeout=1.0
                )
            except Exception as e:
                logger.error(f"Failed to initialize Redis client: {e}")
                self.redis_client = None
        return self.redis_client

    async def dispatch(self, request: Request, call_next):
        global REDIS_FALLBACK_ACTIVE
        if request.url.path in self._BYPASS_PATHS or settings.BILGEAPI_AUTH_MODE == "disabled":
            return await call_next(request)
            
        client_ip = request.client.host if request.client else "unknown"
        if settings.APP_ENV != "production" and request.headers.get("x-test-clear-limits") == "true":
            self.history[client_ip] = deque()
            redis_client = self._get_redis_client()
            if redis_client:
                try:
                    for key in redis_client.scan_iter("bilgeapi:rate_limit:*"):
                        redis_client.delete(key)
                except Exception:
                    pass
            
        now = time.time()
        
        use_fallback = True
        redis_client = self._get_redis_client()
        if redis_client:
            try:
                current_second = int(now)
                key = f"bilgeapi:rate_limit:{client_ip}:{current_second}"
                
                # Check current count in a pipeline
                pipe = redis_client.pipeline()
                pipe.incr(key)
                pipe.expire(key, 2)
                res = pipe.execute()
                
                current_requests = res[0]
                if current_requests > settings.BILGEAPI_RATE_LIMIT_RPS:
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Too many requests. Please try again later."}
                    )
                use_fallback = False
                REDIS_FALLBACK_ACTIVE = False
            except Exception as e:
                # Redis failed -> Fallback to in-memory rate limiter
                if not self._redis_fallback_logged:
                    logger.warning(f"Redis rate limiter unavailable, falling back to in-memory: {e}")
                    self._redis_fallback_logged = True
                
                REDIS_FALLBACK_ACTIVE = True
                
                if _PROMETHEUS_AVAILABLE and REDIS_FALLBACK_COUNT:
                    REDIS_FALLBACK_COUNT.inc()
                    
        if use_fallback:
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


# ── Usage Metering Middleware ─────────────────────────────────────────────────
def extract_tenant_id(request: Request) -> str:
    # 1. Try JWT claim
    auth_header = request.headers.get("Authorization")
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
    else:
        token = request.cookies.get("access_token")
        
    if token:
        import jwt
        for secret in settings.BILGEAPI_JWT_SECRETS:
            try:
                payload = jwt.decode(token, secret, algorithms=["HS256"])
                tenant_id = payload.get("tenant_id")
                if tenant_id:
                    return str(tenant_id)
                break  # successfully decoded but no tenant_id, so stop checking other secrets
            except Exception:
                pass
                
    # 2. Try API key metadata / role mapping
    api_key = request.headers.get("X-API-Key")
    if api_key:
        from apps.bilgeapi.auth import parse_static_keys, parse_static_key_hashes
        import hashlib
        import hmac
        key_roles = parse_static_keys()
        hash_roles = parse_static_key_hashes()
        
        api_key_hash = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
        role = None
        for h, r in hash_roles.items():
            if hmac.compare_digest(api_key_hash, h):
                role = r
                break
        if not role:
            for k, r in key_roles.items():
                if hmac.compare_digest(api_key, k):
                    role = r
                    break
        if role:
            return f"role-{role.lower()}"
            
    # 3. Try X-Tenant-ID header (fallback/dev/trusted gateway only)
    x_tenant_id = request.headers.get("X-Tenant-ID")
    if x_tenant_id and settings.APP_ENV != "production":
        return x_tenant_id
        
    return "anonymous"


class UsageMeteringMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        tenant_id = "anonymous"
        try:
            identity = getattr(request.state, "identity", None)
            if isinstance(identity, dict) and identity.get("tenant_id"):
                tenant_id = str(identity["tenant_id"])
            else:
                tenant_id = extract_tenant_id(request)
        except Exception as e:
            logger.warning(f"Error extracting tenant ID: {e}")
            
        if _PROMETHEUS_AVAILABLE and TENANT_REQUESTS:
            try:
                TENANT_REQUESTS.labels(tenant_id=tenant_id).inc()
            except Exception as e:
                logger.warning(f"Error incrementing tenant requests metric: {e}")
                
        # Mask credentials in logs
        path = sanitize_path(request.url.path)
        logger.info(f"[METERING] Tenant: {tenant_id} | Path: {path} | Method: {request.method}")
        return response

app.add_middleware(UsageMeteringMiddleware)


# ── Register Routers ──────────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(metrics_router.router)
app.include_router(catalog.router)
app.include_router(incidents.router)
app.include_router(audit.router)
app.include_router(diagnostics.router)
app.include_router(repairs.router)
app.include_router(release.router)
app.include_router(adapters.router)
app.include_router(admin_api_keys.router)
app.include_router(improvements.router)
app.include_router(review_ledger.router)
app.include_router(system_watchdog.router)


# ── Custom OpenAPI Generator ──────────────────────────────────────────────────
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
    _PUBLIC_PATHS = {"/health", "/docs", "/redoc", "/openapi.json", "/metrics"}
    for path, path_info in openapi_schema.get("paths", {}).items():
        if path in _PUBLIC_PATHS:
            continue
        for method in path_info:
            path_info[method]["security"] = [
                {"ApiKeyHeader": []},
                {"BearerAuth": []}
            ]
            
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
