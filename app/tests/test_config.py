"""Tests for application configuration and settings."""

import os
from unittest.mock import patch

from app.config import Settings, get_settings


class TestCORSConfiguration:
    """Test suite for CORS configuration parsing."""

    def test_cors_origins_wildcard(self):
        """Test CORS origins with wildcard configuration."""
        with patch.dict(os.environ, {"CORS_ORIGINS": "*"}):
            settings = Settings()
            origins = settings.get_cors_origins_list()
            assert origins == ["*"]

    def test_cors_origins_single_origin(self):
        """Test CORS origins with a single origin."""
        with patch.dict(os.environ, {"CORS_ORIGINS": "http://localhost:3000"}):
            settings = Settings()
            origins = settings.get_cors_origins_list()
            assert origins == ["http://localhost:3000"]

    def test_cors_origins_multiple_origins(self):
        """Test CORS origins with multiple comma-separated origins."""
        test_origins = "http://localhost:3000,http://localhost:8080,https://example.com"
        with patch.dict(os.environ, {"CORS_ORIGINS": test_origins}):
            settings = Settings()
            origins = settings.get_cors_origins_list()
            assert len(origins) == 3
            assert "http://localhost:3000" in origins
            assert "http://localhost:8080" in origins
            assert "https://example.com" in origins

    def test_cors_origins_with_spaces(self):
        """Test CORS origins parsing with extra spaces."""
        test_origins = "http://localhost:3000 , http://localhost:8080 , https://example.com"
        with patch.dict(os.environ, {"CORS_ORIGINS": test_origins}):
            settings = Settings()
            origins = settings.get_cors_origins_list()
            assert len(origins) == 3
            assert "http://localhost:3000" in origins
            assert "http://localhost:8080" in origins
            assert "https://example.com" in origins

    def test_cors_origins_empty_values_filtered(self):
        """Test that empty values are filtered out from origins."""
        test_origins = "http://localhost:3000,,http://localhost:8080"
        with patch.dict(os.environ, {"CORS_ORIGINS": test_origins}):
            settings = Settings()
            origins = settings.get_cors_origins_list()
            assert len(origins) == 2
            assert "" not in origins

    def test_cors_methods_wildcard(self):
        """Test CORS methods with wildcard configuration."""
        with patch.dict(os.environ, {"CORS_ALLOW_METHODS": "*"}):
            settings = Settings()
            methods = settings.get_cors_methods_list()
            assert methods == ["*"]

    def test_cors_methods_specific(self):
        """Test CORS methods with specific HTTP methods."""
        test_methods = "GET,POST,PUT,DELETE,OPTIONS"
        with patch.dict(os.environ, {"CORS_ALLOW_METHODS": test_methods}):
            settings = Settings()
            methods = settings.get_cors_methods_list()
            assert len(methods) == 5
            assert "GET" in methods
            assert "POST" in methods
            assert "PUT" in methods
            assert "DELETE" in methods
            assert "OPTIONS" in methods

    def test_cors_headers_wildcard(self):
        """Test CORS headers with wildcard configuration."""
        with patch.dict(os.environ, {"CORS_ALLOW_HEADERS": "*"}):
            settings = Settings()
            headers = settings.get_cors_headers_list()
            assert headers == ["*"]

    def test_cors_headers_specific(self):
        """Test CORS headers with specific header names."""
        test_headers = "Content-Type,Authorization,X-Custom-Header"
        with patch.dict(os.environ, {"CORS_ALLOW_HEADERS": test_headers}):
            settings = Settings()
            headers = settings.get_cors_headers_list()
            assert len(headers) == 3
            assert "Content-Type" in headers
            assert "Authorization" in headers
            assert "X-Custom-Header" in headers

    def test_cors_allow_credentials_true(self):
        """Test CORS allow credentials set to true."""
        with patch.dict(os.environ, {"CORS_ALLOW_CREDENTIALS": "True"}):
            settings = Settings()
            assert settings.cors_allow_credentials is True

    def test_cors_allow_credentials_false(self):
        """Test CORS allow credentials set to false."""
        with patch.dict(os.environ, {"CORS_ALLOW_CREDENTIALS": "False"}):
            settings = Settings()
            assert settings.cors_allow_credentials is False

    def test_cors_default_values(self):
        """Test that CORS configuration has sensible defaults in the model."""
        # The Settings class defines defaults for CORS fields.
        # We verify those defaults are set correctly in the Field definitions.
        # Note: In practice, .env file may override these, but we test the model defaults.

        # Check that the Field defaults are correct by inspecting the model fields
        cors_origins_field = Settings.model_fields.get("cors_origins")
        cors_credentials_field = Settings.model_fields.get("cors_allow_credentials")
        cors_methods_field = Settings.model_fields.get("cors_allow_methods")
        cors_headers_field = Settings.model_fields.get("cors_allow_headers")

        assert cors_origins_field is not None
        assert cors_credentials_field is not None
        assert cors_methods_field is not None
        assert cors_headers_field is not None

        # Verify the default values in the model schema
        assert cors_origins_field.default == "*"
        assert cors_credentials_field.default is False  # Secure by default
        assert cors_methods_field.default == "*"
        assert cors_headers_field.default == "*"


class TestSettingsIntegration:
    """Integration tests for Settings class."""

    def test_get_settings_returns_settings_instance(self):
        """Test that get_settings returns a Settings instance."""
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_settings_has_cors_configuration(self):
        """Test that settings instance has CORS configuration."""
        settings = get_settings()
        assert hasattr(settings, "cors_origins")
        assert hasattr(settings, "cors_allow_credentials")
        assert hasattr(settings, "cors_allow_methods")
        assert hasattr(settings, "cors_allow_headers")
        assert hasattr(settings, "get_cors_origins_list")
        assert hasattr(settings, "get_cors_methods_list")
        assert hasattr(settings, "get_cors_headers_list")
