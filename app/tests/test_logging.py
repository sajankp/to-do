import uuid

import structlog
from fastapi import FastAPI
from fastapi.testclient import TestClient
from structlog.testing import capture_logs

from app.middleware.logging import StructlogMiddleware
from app.routers.auth import create_token

# Setup minimal app for testing middleware
app = FastAPI()
app.add_middleware(StructlogMiddleware)


@app.get("/test")
def test_endpoint():
    # Return the bound context variables for verification
    return structlog.contextvars.get_contextvars()


client = TestClient(app)


def test_request_id_header():
    """Verify X-Request-ID header is added to response."""
    response = client.get("/test")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    # Verify it matches the bound context
    data = response.json()
    assert data["request_id"] == response.headers["X-Request-ID"]


def test_sid_context_extraction():
    """Verify sid is extracted from valid token and bound to context."""
    sid = str(uuid.uuid4())
    token = create_token(data={"sub": "testuser"}, sid=sid)

    response = client.get("/test", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()

    assert "sid" in data
    assert data["sid"] == sid
    assert data["client_ip"] == "testclient"
    assert data["method"] == "GET"
    assert data["path"] == "/test"


def test_request_logging_execution():
    """Verify middleware executes logging without errors."""
    with capture_logs() as cap_logs:
        client.get("/test")

    # Check for "Request finished" event
    # We can't check context vars here easily due to capture_logs behavior,
    # but we can check the event itself was logged.
    finish_log = next(
        (log_entry for log_entry in cap_logs if log_entry.get("event") == "Request finished"), None
    )
    assert finish_log is not None
    assert "duration" in finish_log
    assert "status_code" in finish_log
    assert finish_log["status_code"] == 200
