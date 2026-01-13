from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.security import SecurityHeadersMiddleware


def test_security_headers_present():
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/")
    def read_root():
        return {"message": "Hello World"}

    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-XSS-Protection"] == "1; mode=block"
    assert "max-age=31536000" in response.headers["Strict-Transport-Security"]
    assert "default-src 'self'" in response.headers["Content-Security-Policy"]
