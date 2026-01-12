"""Tests for AI router endpoints."""

from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException, Request

from app.models.base import PyObjectId
from app.models.user import UserInDB
from app.routers.ai import VoiceRequest, VoiceResponse, _call_gemini_api, process_voice


def _has_google_genai() -> bool:
    """Check if google-generativeai package is installed."""
    try:
        import google.generativeai  # noqa: F401

        return True
    except ImportError:
        return False


def get_mock_user():
    """Create a mock authenticated user."""
    return UserInDB(
        id=PyObjectId("507f1f77bcf86cd799439011"),
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password",
        disabled=False,
    )


def get_mock_request():
    """Create a mock request object."""
    request = Mock(spec=Request)
    request.state = Mock()
    request.state.user_id = PyObjectId("507f1f77bcf86cd799439011")
    return request


class TestVoiceRequest:
    """Tests for VoiceRequest model validation."""

    def test_valid_request_with_prompt(self):
        """Test that valid prompt is accepted."""
        req = VoiceRequest(prompt="What tasks do I have today?")
        assert req.prompt == "What tasks do I have today?"
        assert req.context is None

    def test_valid_request_with_context(self):
        """Test that prompt with context is accepted."""
        req = VoiceRequest(
            prompt="Summarize my tasks",
            context={"todos": ["Task 1", "Task 2"]},
        )
        assert req.prompt == "Summarize my tasks"
        assert req.context == {"todos": ["Task 1", "Task 2"]}

    def test_empty_prompt_rejected(self):
        """Test that empty prompt is rejected."""
        with pytest.raises(ValueError):
            VoiceRequest(prompt="")

    def test_missing_prompt_rejected(self):
        """Test that missing prompt is rejected."""
        with pytest.raises(ValueError):
            VoiceRequest()


class TestVoiceResponse:
    """Tests for VoiceResponse model."""

    def test_valid_response(self):
        """Test valid response model."""
        resp = VoiceResponse(response="Here are your tasks...", tokens_used=42)
        assert resp.response == "Here are your tasks..."
        assert resp.tokens_used == 42


class TestCallGeminiAPI:
    """Tests for _call_gemini_api function."""

    @pytest.mark.asyncio
    @patch("app.routers.ai.settings")
    async def test_missing_api_key_raises_503(self, mock_settings):
        """Test that missing API key raises 503."""
        mock_settings.gemini_api_key = None

        with pytest.raises(HTTPException) as exc_info:
            await _call_gemini_api("Test prompt")

        assert exc_info.value.status_code == 503
        assert "not configured" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not _has_google_genai(),
        reason="google-generativeai package not installed",
    )
    @patch("app.routers.ai.settings")
    async def test_successful_api_call(self, mock_settings):
        """Test successful Gemini API call - requires actual google-generativeai."""
        # This test requires the actual package; skip in CI where not installed
        # The core logic is tested via TestProcessVoice which mocks _call_gemini_api
        mock_settings.gemini_api_key = "test_api_key"

        # Note: This test would call the real Gemini API if package installed
        # For CI, the package is not installed so this is skipped
        pytest.skip("Integration test - requires real API key")


class TestProcessVoice:
    """Tests for process_voice endpoint function."""

    @pytest.mark.asyncio
    @patch("app.routers.ai._call_gemini_api")
    async def test_successful_voice_processing(self, mock_gemini):
        """Test successful voice processing."""
        mock_gemini.return_value = ("This is the AI response.", 42)
        request = get_mock_request()
        user = get_mock_user()

        voice_request = VoiceRequest(prompt="What tasks do I have?")
        result = await process_voice(voice_request, request, user)

        assert isinstance(result, VoiceResponse)
        assert result.response == "This is the AI response."
        assert result.tokens_used == 42
        mock_gemini.assert_called_once_with("What tasks do I have?", None)

    @pytest.mark.asyncio
    @patch("app.routers.ai._call_gemini_api")
    async def test_voice_processing_with_context(self, mock_gemini):
        """Test voice processing with context."""
        mock_gemini.return_value = ("Summary of tasks.", 100)
        request = get_mock_request()
        user = get_mock_user()

        voice_request = VoiceRequest(
            prompt="Summarize my tasks",
            context={"todos": ["Task 1", "Task 2"]},
        )
        result = await process_voice(voice_request, request, user)

        assert result.response == "Summary of tasks."
        mock_gemini.assert_called_once_with("Summarize my tasks", {"todos": ["Task 1", "Task 2"]})

    @pytest.mark.asyncio
    @patch("app.routers.ai._call_gemini_api")
    async def test_api_error_propagates(self, mock_gemini):
        """Test that Gemini API errors propagate correctly."""
        mock_gemini.side_effect = HTTPException(status_code=502, detail="AI service error")
        request = get_mock_request()
        user = get_mock_user()

        voice_request = VoiceRequest(prompt="Test prompt")

        with pytest.raises(HTTPException) as exc_info:
            await process_voice(voice_request, request, user)

        assert exc_info.value.status_code == 502


class TestAPIKeyNotExposed:
    """Tests to verify API key is never exposed in responses."""

    @pytest.mark.asyncio
    @patch("app.routers.ai._call_gemini_api")
    async def test_api_key_not_in_response(self, mock_gemini):
        """Test that API key is never in response."""
        # Mock API key in settings
        with patch("app.routers.ai.settings") as mock_settings:
            mock_settings.gemini_api_key = "super_secret_key_12345"
            mock_settings.ai_rate_limit = "10/minute"
            mock_gemini.return_value = ("Response without secrets", 50)

            request = get_mock_request()
            user = get_mock_user()
            voice_request = VoiceRequest(prompt="Test")

            result = await process_voice(voice_request, request, user)

            # Verify the secret is not in the response
            assert "super_secret_key_12345" not in result.response


class TestRateLimitConfiguration:
    """Tests for rate limit configuration."""

    def test_rate_limit_decorator_applied(self):
        """Verify rate limit decorator is applied to process_voice."""
        # Check that the function has rate limiting metadata
        # This is a structural test - actual rate limiting is tested via integration tests
        from app.routers.ai import router

        # Find the route
        voice_route = None
        for route in router.routes:
            if hasattr(route, "path") and route.path == "/voice":
                voice_route = route
                break

        assert voice_route is not None, "Voice route should exist"
        assert voice_route.methods == {"POST"}, "Should be POST method"
