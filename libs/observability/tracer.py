"""
libs/observability/tracer.py — Phase 13.04 OTel Tracing Core

Provides:
  - get_tracer(name)          : OpenTelemetry Tracer (no-op if SDK not installed)
  - span(name, **attrs)       : context-manager shortcut
  - set_span_attrs(**kw)      : add attributes to current span
  - inject_headers(carrier)   : W3C trace-context propagation for outgoing HTTP
  - extract_context(carrier)  : extract incoming W3C trace context
  - correlation_id()          : returns current trace_id:span_id string

Design: Soft-dependency on opentelemetry-sdk.
If the SDK is not installed, all calls become no-ops — the platform never crashes
because of missing observability packages.
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Dict, Generator, Optional

# ─── Service metadata ─────────────────────────────────────────────────────────
SERVICE_NAME    = os.getenv("OTEL_SERVICE_NAME", "sovereign-agi")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "13.04")
OTEL_ENDPOINT   = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
OTEL_ENABLED    = os.getenv("OTEL_ENABLED", "true").lower() in ("1", "true", "yes")

# ─── Try to import OTel SDK ───────────────────────────────────────────────────
_OTEL_AVAILABLE = False

try:
    if OTEL_ENABLED:
        from opentelemetry import trace as _ot_trace
        from opentelemetry import context as _ot_context
        from opentelemetry.sdk.trace import TracerProvider as _TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor as _BatchSpanProcessor
        from opentelemetry.sdk.resources import Resource as _Resource
        from opentelemetry.semconv.resource import ResourceAttributes as _ResAttr
        from opentelemetry.propagate import inject as _inject, extract as _extract
        from opentelemetry.trace.propagation.tracecontext import (
            TraceContextTextMapPropagator as _Propagator,
        )

        # Try OTLP gRPC exporter first, fall back to HTTP
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                OTLPSpanExporter as _Exporter,
            )
            _exporter_kwargs: Dict[str, Any] = {"endpoint": OTEL_ENDPOINT, "insecure": True}
        except ImportError:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                OTLPSpanExporter as _Exporter,
            )
            http_ep = OTEL_ENDPOINT.replace(":4317", ":4318")
            _exporter_kwargs = {"endpoint": f"{http_ep}/v1/traces"}

        _resource = _Resource.create({
            _ResAttr.SERVICE_NAME:    SERVICE_NAME,
            _ResAttr.SERVICE_VERSION: SERVICE_VERSION,
            "deployment.environment": os.getenv("APP_ENV", "development"),
        })

        _provider = _TracerProvider(resource=_resource)
        _provider.add_span_processor(
            _BatchSpanProcessor(_Exporter(**_exporter_kwargs))
        )
        _ot_trace.set_tracer_provider(_provider)
        _propagator = _Propagator()
        _OTEL_AVAILABLE = True

except Exception:
    pass  # OTel not installed — all calls become no-ops


# ─── Public API ───────────────────────────────────────────────────────────────

def get_tracer(name: str = SERVICE_NAME):
    """Return an OTel Tracer. Returns a no-op if SDK is not available."""
    if not _OTEL_AVAILABLE:
        return _NoOpTracer()
    return _ot_trace.get_tracer(name, schema_url="https://opentelemetry.io/schemas/1.23.0")


@contextmanager
def span(
    name: str,
    tracer_name: str = SERVICE_NAME,
    attributes: Optional[Dict[str, Any]] = None,
    record_exceptions: bool = True,
) -> Generator:
    """
    Convenience context manager for manual spans.

    Usage:
        with span("my.operation", attributes={"project.id": project_id}) as s:
            s.set_attribute("extra", "value")
            do_work()
    """
    if not _OTEL_AVAILABLE:
        yield _NoOpSpan()
        return

    tracer = get_tracer(tracer_name)
    with tracer.start_as_current_span(
        name,
        attributes=attributes or {},
        record_exception=record_exceptions,
        set_status_on_exception=True,
    ) as s:
        yield s


def set_span_attrs(**kwargs: Any) -> None:
    """Add attributes to the currently active span (no-op safe)."""
    if not _OTEL_AVAILABLE:
        return
    current = _ot_trace.get_current_span()
    if current and current.is_recording():
        for k, v in kwargs.items():
            current.set_attribute(str(k), v)


def inject_headers(carrier: Dict[str, str]) -> Dict[str, str]:
    """Inject W3C traceparent/tracestate headers into `carrier` dict."""
    if not _OTEL_AVAILABLE:
        return carrier
    _inject(carrier)
    return carrier


def extract_context(carrier: Dict[str, str]):
    """Extract OTel context from incoming carrier (e.g. HTTP headers)."""
    if not _OTEL_AVAILABLE:
        return None
    return _extract(carrier)


def correlation_id() -> str:
    """Return 'traceId:spanId' string for log correlation."""
    if not _OTEL_AVAILABLE:
        return "no-otel"
    try:
        ctx = _ot_trace.get_current_span().get_span_context()
        if ctx and ctx.is_valid:
            return f"{ctx.trace_id:032x}:{ctx.span_id:016x}"
    except Exception:
        pass
    return "no-span"


def add_span_event(name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
    """Add an event (log point) to the current span."""
    if not _OTEL_AVAILABLE:
        return
    try:
        _ot_trace.get_current_span().add_event(name, attributes=attributes or {})
    except Exception:
        pass


# ─── No-op Stubs ──────────────────────────────────────────────────────────────

class _NoOpSpan:
    def set_attribute(self, *a, **kw): pass
    def add_event(self, *a, **kw): pass
    def record_exception(self, *a, **kw): pass
    def set_status(self, *a, **kw): pass
    def __enter__(self): return self
    def __exit__(self, *a): pass

class _NoOpTracer:
    @contextmanager
    def start_as_current_span(self, *a, **kw):
        yield _NoOpSpan()
    def start_span(self, *a, **kw): return _NoOpSpan()
