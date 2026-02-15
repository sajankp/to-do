"""Tests for CORS (Cross-Origin Resource Sharing) middleware configuration."""

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def settings():
    """Get current settings for verification."""
    return get_settings()


class TestCORSMiddleware:
    """Test suite for CORS middleware functionality."""

    def test_cors_headers_present_on_get_request(self, client, settings):
        """Test that CORS headers are present on GET requests from allowed origin."""
        # Use an origin that should be allowed based on settings
        allowed_origins = settings.get_cors_origins_list()
        test_origin = allowed_origins[0] if allowed_origins[0] != "*" else "http://localhost:3000"

        response = client.get("/", headers={"Origin": test_origin})
        assert response.status_code == 200
        assert any(h.lower() == "access-control-allow-origin" for h in response.headers)

    def test_cors_allow_credentials_header_matches_config(self, client, settings):
        """Test that allow-credentials header matches the configured value."""
        allowed_origins = settings.get_cors_origins_list()
        test_origin = allowed_origins[0] if allowed_origins[0] != "*" else "http://localhost:3000"

        response = client.get("/", headers={"Origin": test_origin})
        assert response.status_code == 200

        credentials_header = response.headers.get("access-control-allow-credentials")

        # If credentials are enabled, header should be 'true'; otherwise absent or 'false'
        if settings.cors_allow_credentials:
            assert credentials_header == "true"
        else:
            assert credentials_header in (None, "false")

    def test_cors_with_allowed_origins(self, client, settings):
        """Test CORS with origins that should be allowed based on configuration."""
        allowed_origins = settings.get_cors_origins_list()

        if "*" in allowed_origins:
            # Wildcard: any origin should work
            test_origins = [
                "http://localhost:3000",
                "http://localhost:8080",
                "https://example.com",
            ]
        else:
            # Specific origins: only those should work
            test_origins = allowed_origins

        for origin in test_origins:
            response = client.get("/", headers={"Origin": origin})
            assert response.status_code == 200
            assert any(
                h.lower() == "access-control-allow-origin" for h in response.headers
            ), f"Origin {origin} should be allowed but didn't get CORS headers"

    def test_cors_on_public_endpoint(self, client, settings):
        """Test CORS on public endpoints."""
        allowed_origins = settings.get_cors_origins_list()
        test_origin = allowed_origins[0] if allowed_origins[0] != "*" else "http://localhost:3000"

        response = client.get("/", headers={"Origin": test_origin})
        assert response.status_code == 200
        assert any(h.lower() == "access-control-allow-origin" for h in response.headers)

    def test_cors_preflight_request_on_token_endpoint(self, client, settings):
        """Test CORS preflight OPTIONS request on token endpoint."""
        allowed_origins = settings.get_cors_origins_list()
        test_origin = allowed_origins[0] if allowed_origins[0] != "*" else "http://localhost:3000"

        response = client.options(
            "/token",
            headers={
                "Origin": test_origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        # Preflight requests should return 200
        assert response.status_code == 200
        assert any(h.lower() == "access-control-allow-origin" for h in response.headers)
        assert any(h.lower() == "access-control-allow-methods" for h in response.headers)

    def test_cors_on_user_creation_endpoint(self, client, settings):
        """Test CORS on user creation endpoint (public endpoint)."""
        allowed_origins = settings.get_cors_origins_list()
        test_origin = allowed_origins[0] if allowed_origins[0] != "*" else "http://localhost:3000"

        response = client.options(
            "/user",
            headers={
                "Origin": test_origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert response.status_code == 200
        assert any(h.lower() == "access-control-allow-origin" for h in response.headers)

    def test_cors_headers_include_allow_methods(self, client, settings):
        """Test that CORS headers include allowed methods."""
        allowed_origins = settings.get_cors_origins_list()
        test_origin = allowed_origins[0] if allowed_origins[0] != "*" else "http://localhost:3000"

        response = client.options(
            "/",
            headers={
                "Origin": test_origin,
                "Access-Control-Request-Method": "GET",
            },
        )
        assert any(h.lower() == "access-control-allow-methods" for h in response.headers)

    def test_cors_headers_include_allow_headers(self, client, settings):
        """Test that CORS headers include allowed headers."""
        allowed_origins = settings.get_cors_origins_list()
        test_origin = allowed_origins[0] if allowed_origins[0] != "*" else "http://localhost:3000"

        response = client.options(
            "/",
            headers={
                "Origin": test_origin,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "content-type,authorization",
            },
        )
        assert any(h.lower() == "access-control-allow-headers" for h in response.headers)

    def test_cors_on_root_endpoint(self, client, settings):
        """Test CORS on root endpoint."""
        allowed_origins = settings.get_cors_origins_list()
        test_origin = allowed_origins[0] if allowed_origins[0] != "*" else "http://localhost:3000"

        response = client.get("/", headers={"Origin": test_origin})
        assert response.status_code == 200
        assert any(h.lower() == "access-control-allow-origin" for h in response.headers)
        assert response.json() == {"message": "Hello, World!"}

    def test_cors_without_origin_header(self, client):
        """Test that requests without Origin header still work."""
        response = client.get("/")
        assert response.status_code == 200
        # CORS headers may or may not be present without Origin header
        # This is expected behavior

    def test_cors_preflight_with_multiple_headers(self, client, settings):
        """Test preflight request with multiple requested headers."""
        allowed_origins = settings.get_cors_origins_list()
        test_origin = allowed_origins[0] if allowed_origins[0] != "*" else "http://localhost:3000"

        response = client.options(
            "/token",
            headers={
                "Origin": test_origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type,authorization,x-custom-header",
            },
        )
        assert response.status_code == 200
        assert any(h.lower() == "access-control-allow-headers" for h in response.headers)

    def test_cors_config_strips_path_and_trailing_slash(self, settings):
        """Test that get_cors_origins_list strips paths and trailing slashes."""
        # Manually set the config to the problematic value reported by user
        settings.cors_origins = (
            "https://to-do-4w0k.onrender.com/, https://sajankp.github.io/to-do-frontend/"
        )

        origins = settings.get_cors_origins_list()

        # Use explicit iteration to satisfy sensitive static analysis listeners
        # Although 'in' on a list is exact, CodeQL might be flagging the string literal relationship
        assert any(o == "https://to-do-4w0k.onrender.com" for o in origins)
        assert not any(o == "https://to-do-4w0k.onrender.com/" for o in origins)

        assert any(o == "https://sajankp.github.io" for o in origins)
        assert not any(o == "https://sajankp.github.io/to-do-frontend/" for o in origins)
