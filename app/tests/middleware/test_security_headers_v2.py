from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.middleware.security import SecurityHeadersMiddleware


def test_headers_on_error_response():
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/error")
    def trigger_error():
        raise HTTPException(status_code=400, detail="Bad Request")

    client = TestClient(app)
    response = client.get("/error")

    assert response.status_code == 400
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Content-Security-Policy"] is not None


def test_hsts_conditional():
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/")
    def read_root():
        return {"msg": "ok"}

    client = TestClient(app)

    # HTTP request -> No HSTS
    response = client.get("/", headers={"x-forwarded-proto": "http"})
    assert "Strict-Transport-Security" not in response.headers

    # HTTPS request -> HSTS present
    response = client.get("/", headers={"x-forwarded-proto": "https"})
    assert "Strict-Transport-Security" in response.headers
