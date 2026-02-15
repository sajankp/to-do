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
    # Check that directives are correctly formed
    # Using set equality avoids CodeQL "Incomplete URL substring sanitization" alerts
    assert directives["style-src"] == {
        "'self'",
        "'unsafe-inline'",
        "https://fonts.googleapis.com",
        "https://cdn.jsdelivr.net/npm/",
    }

    assert directives["script-src"] == {
        "'self'",
        "'unsafe-inline'",
        "https://cdn.jsdelivr.net/npm/",
    }

    assert directives["img-src"] == {
        "'self'",
        "data:",
        "https://fastapi.tiangolo.com",
    }

    assert directives["font-src"] == {"'self'", "https://fonts.gstatic.com"}


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

        # Verify overridden values are present by parsing the CSP string
        directives = {}
        for part in csp.split(";"):
            tokens = part.strip().split()
            if not tokens:
                continue
            directive = tokens[0]
            sources = set(tokens[1:])
            directives[directive] = sources

        assert directives["img-src"] == {"'self'", "data:", "https://img.example.com"}
        assert directives["style-src"] == {"'self'", "'unsafe-inline'", "https://style.example.com"}
        assert directives["script-src"] == {
            "'self'",
            "'unsafe-inline'",
            "https://script.example.com",
        }
        assert directives["font-src"] == {"'self'", "https://font.example.com"}


def test_csp_semicolon_sanitization():
    """Test that semicolons are removed from CSP values to prevent injection."""
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/")
    def read_root():
        return {"msg": "ok"}

    from unittest.mock import patch

    from app.config import Settings

    mock_settings = Settings()
    # Inject a semicolon into a CSP value
    mock_settings.csp_img_src = "https://img.com; script-src 'unsafe-eval'"

    with patch("app.middleware.security.get_settings", return_value=mock_settings):
        client = TestClient(app)
        response = client.get("/")
        csp = response.headers["Content-Security-Policy"]

        # Semicolon should be removed, merging the injected part into the img-src directive
        # instead of creating a new script-src directive.
        assert "img-src 'self' data: https://img.com script-src 'unsafe-eval';" in csp

        # Parse and verify the directives
        directives = {}
        for part in csp.split(";"):
            tokens = part.strip().split()
            if not tokens:
                continue
            directive = tokens[0]
            sources = set(tokens[1:])
            directives[directive] = sources

        # The injected "script-src" should be a source in img-src, NOT a separate directive
        assert "script-src" in directives["img-src"]
        assert "'unsafe-eval'" in directives["img-src"]
        # And the original script-src should still be correct
        assert directives["script-src"] == {
            "'self'",
            "'unsafe-inline'",
            "https://cdn.jsdelivr.net/npm/",
        }
