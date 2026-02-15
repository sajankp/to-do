from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.security import SecurityHeadersMiddleware


def test_csp_directives_specifics():
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/")
    def read_root():
        return {"msg": "ok"}

    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    csp = response.headers["Content-Security-Policy"]

    # Parse CSP into a dictionary for robust checking
    # "default-src 'self'; img-src ..." -> {'default-src': {'self'}, 'img-src': ...}
    directives = {}
    for part in csp.split(";"):
        tokens = part.strip().split()
        if not tokens:
            continue
        directive = tokens[0]
        sources = set(tokens[1:])
        directives[directive] = sources

    # Check that directives are correctly formed
    assert "https://fonts.googleapis.com" in directives["style-src"]
    assert "https://cdn.jsdelivr.net/npm/" in directives["style-src"]
    assert "'unsafe-inline'" in directives["style-src"]
    assert "'self'" in directives["style-src"]

    assert "https://cdn.jsdelivr.net/npm/" in directives["script-src"]
    assert "'unsafe-inline'" in directives["script-src"]
    assert "'self'" in directives["script-src"]

    assert "https://fastapi.tiangolo.com" in directives["img-src"]
    assert "data:" in directives["img-src"]
    assert "'self'" in directives["img-src"]

    assert "https://fonts.gstatic.com" in directives["font-src"]
    assert "'self'" in directives["font-src"]


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
