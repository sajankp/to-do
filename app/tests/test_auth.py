from datetime import timedelta
from unittest.mock import Mock, patch

from app.config import get_settings
from app.routers.auth import create_token

settings = get_settings()
ALLOWED_ORIGIN = "http://localhost:3000"

# Local client fixture removed in favor of conftest.py shared fixture


class TestAuthCookies:
    """Tests for HttpOnly cookie authentication (TD-011/TD-015)."""

    @patch("app.main.authenticate_user")
    def test_login_sets_httponly_cookies(self, mock_auth, client):
        """Test that login response sets HttpOnly cookies."""
        # Mock successful authentication
        mock_user = Mock()
        mock_user.username = "testuser"
        mock_user.id = "507f1f77bcf86cd799439011"
        mock_auth.return_value = (mock_user, None)  # User, new_hash

        response = client.post(
            "/token",
            data={"username": "testuser", "password": "password"},
        )

        assert response.status_code == 200

        # Verify cookies are set
        assert "access_token" in response.cookies
        assert "refresh_token" in response.cookies

        # Verify body DOES NOT contain tokens (they should be None)
        data = response.json()
        assert data["access_token"] is None
        assert data["refresh_token"] is None

        # Verify Cookie Attributes (Strict Security)
        # We need to inspect the raw Set-Cookie header because TestClient.cookies abstracts attributes
        set_cookie_headers = response.headers.get_list("set-cookie")
        assert len(set_cookie_headers) > 0

        # Check access_token cookie
        access_cookie = next((h for h in set_cookie_headers if "access_token=" in h), None)
        assert access_cookie is not None
        assert "HttpOnly" in access_cookie
        assert "SameSite=none" in access_cookie or "SameSite=None" in access_cookie
        assert "Secure" in access_cookie

        # Check refresh_token cookie
        refresh_cookie = next((h for h in set_cookie_headers if "refresh_token=" in h), None)
        assert refresh_cookie is not None
        assert "HttpOnly" in refresh_cookie
        assert "SameSite=none" in refresh_cookie or "SameSite=None" in refresh_cookie
        assert "Secure" in refresh_cookie

    def test_refresh_reads_cookie(self, client):
        """Test that refresh endpoint reads token from cookie."""
        # Create a valid refresh token
        refresh_token = create_token(
            data={"sub": "testuser", "sub_id": "507f1f77bcf86cd799439011"},
            expires_delta=timedelta(minutes=10),
            sid="test-session-id",
            token_type="refresh",
        )

        # Set cookie in client
        client.cookies.set("refresh_token", refresh_token)

        # Mock user retrieval
        with patch("app.main.get_user_by_username") as mock_get_user:
            mock_user = Mock()
            mock_user.username = "testuser"
            mock_user.disabled = False
            mock_get_user.return_value = mock_user

            # Call refresh endpoint WITHOUT body/query params
            response = client.post("/token/refresh", headers={"Origin": ALLOWED_ORIGIN})

            assert response.status_code == 200
            assert "access_token" in response.cookies
            # Body should not contain token
            assert response.json()["access_token"] is None

    def test_logout_clears_cookies(self, client):
        """Test that logout endpoint clears cookies."""
        # Set some initial cookies
        client.cookies.set("access_token", "old_token")
        client.cookies.set("refresh_token", "old_refresh")

        response = client.post("/auth/logout", headers={"Origin": ALLOWED_ORIGIN})

        assert response.status_code == 200

        # Verify cookies are expired/cleared
        # In TestClient, cleared cookies might strictly be removed or set to ""
        # Inspecting Set-Cookie header for Max-Age=0 matches spec.

        set_cookies = response.headers.get("set-cookie")
        assert "access_token=" in set_cookies
        assert "refresh_token=" in set_cookies
        assert "Max-Age=0" in set_cookies or "Expires=" in set_cookies

    def test_cors_allows_credentials(self, client):
        """Test that CORS configuration allows credentials."""
        # This tests the middleware configuration refactor
        print(f"DEBUG: settings.cors_allow_credentials = {settings.cors_allow_credentials}")
        print(f"DEBUG: settings.cors_origins = {settings.cors_origins}")

        # Check CORSMiddleware config in app
        # from fastapi.middleware.cors import CORSMiddleware
        # for middleware in app.user_middleware:
        #    if middleware.cls == CORSMiddleware:
        #         pass

        # Use an origin likely to be in the allowed list (from .env or default)
        # The user's .env has http://localhost:3000.
        response = client.options(
            "/token",
            headers={
                "Origin": ALLOWED_ORIGIN,
                "Access-Control-Request-Method": "POST",
            },
        )

        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == ALLOWED_ORIGIN
        assert response.headers.get("access-control-allow-credentials") == "true"

    def test_refresh_rejects_missing_origin_header(self, client):
        """Refresh endpoint should reject requests without trusted origin."""
        refresh_token = create_token(
            data={"sub": "testuser", "sub_id": "507f1f77bcf86cd799439011"},
            expires_delta=timedelta(minutes=10),
            sid="test-session-id",
            token_type="refresh",
        )
        client.cookies.set("refresh_token", refresh_token)

        with patch("app.main.get_user_by_username") as mock_get_user:
            mock_user = Mock()
            mock_user.username = "testuser"
            mock_user.disabled = False
            mock_get_user.return_value = mock_user

            response = client.post("/token/refresh")

        assert response.status_code == 403
        assert response.json()["detail"] == "CSRF validation failed"

    def test_protected_post_rejects_missing_origin(self, client):
        """Authenticated unsafe requests must include a trusted Origin header."""
        access_token = create_token(
            data={"sub": "testuser", "sub_id": "507f1f77bcf86cd799439011"},
            expires_delta=timedelta(minutes=10),
            sid="test-session-id",
            token_type="access",
        )
        client.cookies.set("access_token", access_token)

        response = client.post("/todo/", json={})

        assert response.status_code == 403
        assert response.json()["detail"] == "CSRF validation failed"
