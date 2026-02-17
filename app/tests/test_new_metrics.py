"""Tests for new Prometheus metrics added in TD-005 completion."""


def test_new_metrics_registered(client):
    """Verify new metrics appear in /metrics output."""
    # Enable dev mode for metrics access
    from app.main import settings

    original_dev_mode = settings.metrics_dev_mode
    settings.metrics_dev_mode = True

    try:
        response = client.get("/metrics")
        assert response.status_code == 200
        content = response.text

        # Verify new metrics are registered
        assert "fasttodo_todos_per_user" in content
        assert "fasttodo_db_connections_active" in content
        assert "fasttodo_db_query_duration_seconds" in content

    finally:
        settings.metrics_dev_mode = original_dev_mode
