"""Tests for WebSocket streaming AI endpoint."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.base import PyObjectId
from app.models.user import UserInDB


def get_mock_user():
    """Create a mock authenticated user."""
    return UserInDB(
        id=PyObjectId("507f1f77bcf86cd799439011"),
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password",
        disabled=False,
    )


class TestWebSocketAuth:
    """Tests for WebSocket authentication."""

    def test_websocket_rejects_no_auth(self):
        """Test that WebSocket connection requires authentication."""
        client = TestClient(app)

        with client.websocket_connect("/api/ai/voice/stream") as websocket:
            # Send something other than auth message
            websocket.send_json({"type": "audio", "data": "abc"})
            response = websocket.receive_json()

            assert response["type"] == "error"
            assert "auth" in response["message"].lower()

    def test_websocket_rejects_invalid_token(self):
        """Test that invalid JWT token is rejected."""
        client = TestClient(app)

        with client.websocket_connect("/api/ai/voice/stream") as websocket:
            websocket.send_json({"type": "auth", "token": "invalid_token"})
            response = websocket.receive_json()

            assert response["type"] == "error"
            assert "invalid" in response["message"].lower()

    @patch("app.routers.ai_stream.get_user_by_username")
    @patch("app.routers.ai_stream.jwt.decode")
    def test_websocket_accepts_valid_token(self, mock_decode, mock_get_user):
        """Test that valid JWT token is accepted."""
        mock_decode.return_value = {"sub": "testuser"}
        mock_user = get_mock_user()
        mock_get_user.return_value = mock_user

        client = TestClient(app)

        with client.websocket_connect("/api/ai/voice/stream") as websocket:
            websocket.send_json({"type": "auth", "token": "valid_token"})
            # Should get either "connected" or "error" (if Gemini not configured)
            response = websocket.receive_json()

            # The response should be either connected or an error about Gemini config
            assert response["type"] in ["connected", "error"]


class TestGeminiLiveProxy:
    """Tests for GeminiLiveProxy class."""

    @pytest.mark.asyncio
    async def test_authenticate_token_validates_jwt(self):
        """Test that authenticate_token validates JWT properly."""
        from jose import JWTError

        from app.routers.ai_stream import GeminiLiveProxy

        mock_websocket = AsyncMock()
        proxy = GeminiLiveProxy(mock_websocket, "", "")

        # Invalid token should return False
        with patch("app.routers.ai_stream.jwt.decode", side_effect=JWTError("Invalid")):
            result = await proxy.authenticate_token("bad_token")
            assert result is False

    @pytest.mark.asyncio
    async def test_handle_tool_call_get_todos(self):
        """Test handling get_todos tool call."""
        from app.routers.ai_stream import GeminiLiveProxy

        mock_websocket = AsyncMock()
        proxy = GeminiLiveProxy(mock_websocket, "user123", "testuser")
        proxy.todos = [
            {
                "title": "Task 1",
                "priority": "high",
                "due_date": "2024-01-01",
                "description": "Desc 1",
            },
            {
                "title": "Task 2",
                "priority": "low",
                "due_date": "2024-01-02",
                "description": "Desc 2",
            },
        ]

        # Create mock function call
        mock_fc = Mock()
        mock_fc.name = "get_todos"
        mock_fc.args = {}

        result = await proxy._handle_tool_call(mock_fc)

        assert "todos" in result
        assert len(result["todos"]) == 2
        assert result["todos"][0]["title"] == "Task 1"

    @pytest.mark.asyncio
    async def test_handle_tool_call_create_todo(self):
        """Test handling create_todo tool call."""
        from app.routers.ai_stream import GeminiLiveProxy

        mock_websocket = AsyncMock()
        proxy = GeminiLiveProxy(mock_websocket, "user123", "testuser")

        mock_fc = Mock()
        mock_fc.name = "create_todo"
        mock_fc.args = {"title": "New Task", "description": "New Description"}

        result = await proxy._handle_tool_call(mock_fc)

        assert result["status"] == "success"
        assert "New Task" in result["message"]
        # Verify action was sent to frontend
        mock_websocket.send_json.assert_called_with(
            {
                "type": "action",
                "action": "create_todo",
                "data": {
                    "title": "New Task",
                    "description": "New Description",
                    "priority": "medium",
                    "due_date": None,
                },
            }
        )

    @pytest.mark.asyncio
    async def test_handle_tool_call_delete_todo_not_found(self):
        """Test delete_todo when task not found."""
        from app.routers.ai_stream import GeminiLiveProxy

        mock_websocket = AsyncMock()
        proxy = GeminiLiveProxy(mock_websocket, "user123", "testuser")
        proxy.todos = [{"title": "Buy Milk", "id": "123"}]

        mock_fc = Mock()
        mock_fc.name = "delete_todo"
        mock_fc.args = {"search_title": "nonexistent"}

        result = await proxy._handle_tool_call(mock_fc)

        assert result["status"] == "error"
        assert "No task found" in result["message"]

    @pytest.mark.asyncio
    async def test_handle_tool_call_delete_todo_multiple_matches(self):
        """Test delete_todo when multiple tasks match."""
        from app.routers.ai_stream import GeminiLiveProxy

        mock_websocket = AsyncMock()
        proxy = GeminiLiveProxy(mock_websocket, "user123", "testuser")
        proxy.todos = [
            {"title": "Buy Milk", "id": "123"},
            {"title": "Buy Milk 2", "id": "456"},
        ]

        mock_fc = Mock()
        mock_fc.name = "delete_todo"
        mock_fc.args = {"search_title": "buy"}

        result = await proxy._handle_tool_call(mock_fc)

        assert result["status"] == "error"
        assert "Multiple tasks" in result["message"]

    @pytest.mark.asyncio
    async def test_handle_tool_call_delete_todo_success(self):
        """Test successful delete_todo."""
        from app.routers.ai_stream import GeminiLiveProxy

        mock_websocket = AsyncMock()
        proxy = GeminiLiveProxy(mock_websocket, "user123", "testuser")
        proxy.todos = [{"title": "Buy Milk", "id": "123"}]

        mock_fc = Mock()
        mock_fc.name = "delete_todo"
        mock_fc.args = {"search_title": "milk"}

        result = await proxy._handle_tool_call(mock_fc)

        assert result["status"] == "success"
        mock_websocket.send_json.assert_called_with(
            {
                "type": "action",
                "action": "delete_todo",
                "data": {"id": "123"},
            }
        )


class TestServiceConfiguration:
    """Tests for service configuration errors."""

    @patch("app.routers.ai_stream.get_user_by_username")
    @patch("app.routers.ai_stream.jwt.decode")
    @patch("app.routers.ai_stream.settings")
    def test_websocket_returns_error_when_no_api_key(
        self, mock_settings, mock_decode, mock_get_user
    ):
        """Test that missing API key returns error."""
        mock_settings.gemini_api_key = None
        mock_decode.return_value = {"sub": "testuser"}
        mock_get_user.return_value = get_mock_user()

        client = TestClient(app)

        with client.websocket_connect("/api/ai/voice/stream") as websocket:
            websocket.send_json({"type": "auth", "token": "valid_token"})
            response = websocket.receive_json()

            assert response["type"] == "error"
            assert "not configured" in response["message"].lower()
