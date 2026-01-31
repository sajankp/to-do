from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_metrics_endpoint_exists():
    """Verify that the /metrics endpoint is exposed."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]


def test_metrics_content_format():
    """Verify that the /metrics endpoint returns Prometheus formatted metrics."""
    response = client.get("/health")  # Generate some traffic
    assert response.status_code == 200

    response = client.get("/metrics")
    assert response.status_code == 200
    content = response.text

    # Standard metrics
    assert "http_requests_total" in content
    assert "http_request_duration_seconds" in content


def test_custom_metrics_registered():
    """Verify that custom metrics are registered and appear in the output."""
    # We expect these metrics to exist even if 0
    response = client.get("/metrics")
    assert response.status_code == 200
    content = response.text

    assert "fasttodo_logins_total" in content
    assert "fasttodo_todos_created_total" in content
    assert "fasttodo_todos_completed_total" in content
    assert "fasttodo_ai_requests_total" in content


def test_login_metric_increment(monkeypatch):
    """Verify fasttodo_logins_total increments on login success and failure."""
    from unittest.mock import Mock

    from app.models.user import UserInDB
    from app.utils.metrics import LOGINS_TOTAL

    # --- Test successful login ---
    initial_count_success = LOGINS_TOTAL.labels(status="success")._value.get()

    # Mock authentication to succeed
    mock_auth_success = Mock(
        return_value=(
            UserInDB(
                username="testuser",
                email="test@example.com",
                hashed_password="hashed",
                id="507f1f77bcf86cd799439011",
            ),
            "new_hash_value",  # Simulate hash migration
        )
    )
    monkeypatch.setattr("app.main.authenticate_user", mock_auth_success)

    # Mock the database update_one call to avoid DB dependency
    from app.main import app

    mock_update_one = Mock(return_value=None)
    if hasattr(app, "user"):
        original_update_one = app.user.update_one
        app.user.update_one = mock_update_one

    response = client.post("/token", data={"username": "testuser", "password": "password"})
    assert response.status_code == 200, response.text
    new_count_success = LOGINS_TOTAL.labels(status="success")._value.get()
    assert new_count_success == initial_count_success + 1

    # Restore if mocked
    if hasattr(app, "user") and "original_update_one" in locals():
        app.user.update_one = original_update_one

    # --- Test failed login ---
    initial_count_failed = LOGINS_TOTAL.labels(status="failed")._value.get()

    # Mock authentication to fa il
    mock_auth_fail = Mock(return_value=(None, None))
    monkeypatch.setattr("app.main.authenticate_user", mock_auth_fail)

    response_fail = client.post("/token", data={"username": "baduser", "password": "badpass"})
    assert response_fail.status_code == 401
    new_count_failed = LOGINS_TOTAL.labels(status="failed")._value.get()
    assert new_count_failed == initial_count_failed + 1
