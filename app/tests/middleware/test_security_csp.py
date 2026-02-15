from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.security import SecurityHeadersMiddleware


def test_csp_includes_required_domains():
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/")
    def read_root():
        return {"msg": "ok"}

    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    csp = response.headers["Content-Security-Policy"]

    # Parse CSP into a flat list of tokens to check for exact presence
    # This avoids "Incomplete URL substring sanitization" alerts from static analysis
    # "default-src 'self'; img-src ..." -> ["default-src", "'self'", "img-src", ...]
    csp_tokens = [t.strip() for directive in csp.split(";") for t in directive.strip().split()]

    # Check for required domains
    assert "https://fonts.googleapis.com" in csp_tokens, "Google Fonts (style) missing"
    assert "https://cdn.jsdelivr.net/npm/" in csp_tokens, "JSDelivr (script/style) missing"
    assert "https://fastapi.tiangolo.com" in csp_tokens, "FastAPI Favicon (img) missing"
    assert "https://fonts.gstatic.com" in csp_tokens, "Google Fonts (font) missing"


def test_csp_directives_specifics():
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/")
    def read_root():
        return {"msg": "ok"}

    client = TestClient(app)
    response = client.get("/")
    csp = response.headers["Content-Security-Policy"]

    # Check that directives are correctly formed
    assert (
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net"
        in csp
    )
    assert "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net" in csp
    assert "img-src 'self' data: https://fastapi.tiangolo.com" in csp
    assert "font-src 'self' https://fonts.gstatic.com" in csp


def test_csp_configuration_override():
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/")
    def read_root():
        return {"msg": "ok"}

    # We need to patch where it is used in the middleware
    from unittest.mock import patch

    from app.config import Settings

    # Create a mock settings object with custom values
    mock_settings = Settings()
    mock_settings.csp_img_src = "https://img.example.com"
    mock_settings.csp_style_src = "https://style.example.com"
    mock_settings.csp_script_src = "https://script.example.com"
    mock_settings.csp_font_src = "https://font.example.com"

    with patch("app.middleware.security.get_settings", return_value=mock_settings):
        client = TestClient(app)
        response = client.get("/")

        assert response.status_code == 200
        csp = response.headers["Content-Security-Policy"]

        # Verify overridden values are present
        assert "img-src 'self' data: https://img.example.com;" in csp
        assert "style-src 'self' 'unsafe-inline' https://style.example.com;" in csp
        assert "script-src 'self' 'unsafe-inline' https://script.example.com;" in csp
        assert "font-src 'self' https://font.example.com;" in csp
