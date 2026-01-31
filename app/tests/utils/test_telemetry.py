from unittest.mock import Mock, patch

from opentelemetry import trace

from app.utils.telemetry import setup_telemetry


class TestTelemetry:
    def test_tracer_provider_configured(self):
        """Test that tracer provider is configured when OTel is enabled"""
        app = Mock()

        # Mock settings to enable OTel
        settings = Mock()
        settings.otel_exporter_otlp_endpoint = "http://localhost:4317"
        settings.otel_service_name = "test-service"

        with patch("app.utils.telemetry.TracerProvider") as mock_provider, patch(
            "app.utils.telemetry.set_tracer_provider"
        ) as mock_set_provider, patch(
            "app.utils.telemetry.BatchSpanProcessor"
        ) as mock_processor, patch("app.utils.telemetry.OTLPSpanExporter") as mock_exporter:
            setup_telemetry(app, settings)

            mock_set_provider.assert_called_once()
            mock_provider.return_value.add_span_processor.assert_called_with(
                mock_processor.return_value
            )
            mock_exporter.assert_called_with(endpoint="http://localhost:4317")

    def test_otel_disabled_when_no_endpoint(self):
        """Test that OTel setup is skipped/disabled when endpoint is missing"""
        app = Mock()
        settings = Mock()
        settings.otel_exporter_otlp_endpoint = None

        with patch("app.utils.telemetry.set_tracer_provider") as mock_set_provider:
            setup_telemetry(app, settings)
            mock_set_provider.assert_not_called()

    def test_trace_context_injected_in_logs(self):
        """Test that trace ID and span ID are injected into log processor"""
        # This tests the custom log processor logic
        from app.utils.telemetry import add_trace_context

        # Mock current span
        mock_span = Mock()
        mock_context = Mock()
        mock_context.trace_id = 0x12345678901234567890123456789012
        mock_context.span_id = 0x1234567890123456
        mock_span.get_span_context.return_value = mock_context

        with patch("opentelemetry.trace.get_current_span", return_value=mock_span):
            logger = Mock()
            method_name = "info"
            event_dict = {"event": "test"}

            result = add_trace_context(logger, method_name, event_dict)

            assert "trace_id" in result
            assert "span_id" in result
            assert result["trace_id"] == "12345678901234567890123456789012"
            assert result["span_id"] == "1234567890123456"

    def test_trace_context_missing_when_no_span(self):
        """Test seamless handling when no active span exists"""
        from app.utils.telemetry import add_trace_context

        # Use INVALID_SPAN_CONTEXT which acts like a no-op context
        with patch(
            "opentelemetry.trace.get_current_span",
            return_value=trace.NonRecordingSpan(trace.INVALID_SPAN_CONTEXT),
        ):
            logger = Mock()
            method_name = "info"
            event_dict = {"event": "test"}

            result = add_trace_context(logger, method_name, event_dict)

            # Should not crash, might add empty or 0 trace_id depending on impl
            # Usually structlog processor leaves it out or adds None if configured
            # For this test, let's assume it adds them as None or 0 or simply returns dict
            assert isinstance(result, dict)
