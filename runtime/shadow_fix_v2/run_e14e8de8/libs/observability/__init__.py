"""libs/observability package — OTel tracing + metrics exports"""
from libs.observability.tracer import (
    get_tracer,
    span,
    set_span_attrs,
    inject_headers,
    extract_context,
    correlation_id,
    add_span_event,
    OTEL_ENABLED,
    _OTEL_AVAILABLE,
)

__all__ = [
    "get_tracer",
    "span",
    "set_span_attrs",
    "inject_headers",
    "extract_context",
    "correlation_id",
    "add_span_event",
    "OTEL_ENABLED",
    "_OTEL_AVAILABLE",
]
