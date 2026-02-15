from typing import Any

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.pymongo import PymongoInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import set_tracer_provider


def _init_tracer_provider(service_name: str, otel_endpoint: str) -> TracerProvider:
    """Initialize and configure the OpenTelemetry tracer provider."""
    # Ensure endpoint has the correct path for HTTP protocol
    if not otel_endpoint.endswith("/v1/traces"):
        otel_endpoint = f"{otel_endpoint.rstrip('/')}/v1/traces"

    # Create tracer provider with service name
    resource = Resource.create(attributes={"service.name": service_name})
    tracer_provider = TracerProvider(resource=resource)

    # Configure OTLP exporter
    otlp_exporter = OTLPSpanExporter(endpoint=otel_endpoint)
    span_processor = BatchSpanProcessor(otlp_exporter)
    tracer_provider.add_span_processor(span_processor)

    # Set as global tracer provider
    set_tracer_provider(tracer_provider)

    return tracer_provider


def setup_telemetry(app: FastAPI, settings: Any) -> None:
    """
    Configure OpenTelemetry and instrument FastAPI.

    Must be called BEFORE the app starts serving requests.
    Call setup_pymongo_telemetry() later, before creating MongoDB client.

    Args:
        app: FastAPI application instance
        settings: Application settings object
    """
    otel_endpoint = getattr(settings, "otel_exporter_otlp_endpoint", None)
    if not otel_endpoint:
        return  # Telemetry disabled

    service_name = getattr(settings, "otel_service_name", "fasttodo")

    # Initialize tracer provider
    tracer_provider = _init_tracer_provider(service_name, otel_endpoint)

    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer_provider)

    # Instrument logging
    LoggingInstrumentor().instrument(tracer_provider=tracer_provider)


def setup_pymongo_telemetry() -> None:
    """
    Instrument PyMongo for MongoDB tracing.

    Must be called BEFORE creating any MongoDB clients,
    but AFTER setup_telemetry() has initialized the tracer provider.
    """
    tracer_provider = trace.get_tracer_provider()
    PymongoInstrumentor().instrument(tracer_provider=tracer_provider)


def add_trace_context(logger: Any, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    """
    Structlog processor to add OTel trace_id and span_id to logs.
    """
    ctx = trace.get_current_span().get_span_context()
    if ctx.is_valid:
        event_dict["trace_id"] = trace.format_trace_id(ctx.trace_id)
        event_dict["span_id"] = trace.format_span_id(ctx.span_id)

    return event_dict
