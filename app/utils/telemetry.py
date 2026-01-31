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


def setup_telemetry(app: FastAPI, settings: Any) -> None:
    """
    Configure OpenTelemetry instrumentation.

    Args:
        app: FastAPI application instance
        settings: Application settings object
    """

    # Only enable if endpoint is configured
    otel_endpoint = getattr(settings, "otel_exporter_otlp_endpoint", None)
    if not otel_endpoint:
        return

    # Check for service name or default
    service_name = getattr(settings, "otel_service_name", "fasttodo")

    # 1. Configure Tracer Provider
    resource = Resource.create(attributes={"service.name": service_name})
    tracer_provider = TracerProvider(resource=resource)
    set_tracer_provider(tracer_provider)

    # 2. Configure Exporter
    otlp_exporter = OTLPSpanExporter(endpoint=otel_endpoint)
    span_processor = BatchSpanProcessor(otlp_exporter)
    tracer_provider.add_span_processor(span_processor)

    # 3. Instrument Libraries
    # FastAPI
    FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer_provider)

    # PyMongo
    PymongoInstrumentor().instrument(tracer_provider=tracer_provider)

    # Logging (connects Python logging to OTel)
    LoggingInstrumentor().instrument(tracer_provider=tracer_provider)


def add_trace_context(logger: Any, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    """
    Structlog processor to add OTel trace_id and span_id to logs.
    """
    span = trace.get_current_span()
    if span == trace.INVALID_SPAN:
        return event_dict

    ctx = span.get_span_context()
    if ctx.is_valid:
        event_dict["trace_id"] = trace.format_trace_id(ctx.trace_id)
        event_dict["span_id"] = trace.format_span_id(ctx.span_id)

    return event_dict
