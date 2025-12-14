"""Tests for CORS (Cross-Origin Resource Sharing) middleware configuration."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


class TestCORSMiddleware:
    """Test suite for CORS middleware functionality."""

    def test_cors_headers_present_on_get_request(self, client):
        """Test that CORS headers are present on GET requests."""
        response = client.get("/", headers={"Origin": "http://localhost:3000"})
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

    def test_cors_allow_credentials_header(self, client):
        """Test that allow-credentials header is set correctly."""
        response = client.get("/", headers={"Origin": "http://localhost:3000"})
        assert response.status_code == 200
        # Check if credentials are allowed (should be 'true' as string in header)
        credentials_header = response.headers.get("access-control-allow-credentials")
        assert credentials_header is not None

    def test_cors_with_different_origins(self, client):
        """Test CORS with different origin values."""
        origins = [
            "http://localhost:3000",
            "http://localhost:8080",
            "https://example.com",
        ]

        for origin in origins:
            response = client.get("/", headers={"Origin": origin})
            assert response.status_code == 200
            assert "access-control-allow-origin" in response.headers

    def test_cors_on_public_endpoint(self, client):
        """Test CORS on public endpoints."""
        response = client.get("/", headers={"Origin": "http://localhost:3000"})
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

    def test_cors_preflight_request_on_token_endpoint(self, client):
        """Test CORS preflight OPTIONS request on token endpoint."""
        response = client.options(
            "/token",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        # Preflight requests should return 200
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers

    def test_cors_on_user_creation_endpoint(self, client):
        """Test CORS on user creation endpoint (public endpoint)."""
        response = client.options(
            "/user",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

    def test_cors_headers_include_allow_methods(self, client):
        """Test that CORS headers include allowed methods."""
        response = client.options(
            "/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert "access-control-allow-methods" in response.headers

    def test_cors_headers_include_allow_headers(self, client):
        """Test that CORS headers include allowed headers."""
        response = client.options(
            "/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "content-type,authorization",
            },
        )
        assert "access-control-allow-headers" in response.headers

    def test_cors_on_root_endpoint(self, client):
        """Test CORS on root endpoint."""
        response = client.get("/", headers={"Origin": "http://localhost:3000"})
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert response.json() == {"message": "Hello, World!"}

    def test_cors_without_origin_header(self, client):
        """Test that requests without Origin header still work."""
        response = client.get("/")
        assert response.status_code == 200
        # CORS headers may or may not be present without Origin header
        # This is expected behavior

    def test_cors_preflight_with_multiple_headers(self, client):
        """Test preflight request with multiple requested headers."""
        response = client.options(
            "/token",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type,authorization,x-custom-header",
            },
        )
        assert response.status_code == 200
        assert "access-control-allow-headers" in response.headers
