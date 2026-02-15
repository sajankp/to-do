from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import WebSocket, WebSocketDisconnect
from jose import JWTError

from app.routers.ai_stream import GeminiLiveProxy, voice_stream


class TestGeminiLiveProxy:
    def setup_method(self):
        self.mock_ws = AsyncMock(spec=WebSocket)
        self.proxy = GeminiLiveProxy(self.mock_ws, "user_id", "username")

    @pytest.mark.asyncio
    @patch("app.routers.ai_stream.jwt.decode")
    @patch("app.routers.ai_stream.get_user_by_username")
    async def test_authenticate_token_success(self, mock_get_user, mock_info):
        mock_info.return_value = {"sub": "testuser"}
        mock_user = Mock()
        mock_user.id = "user123"
        mock_get_user.return_value = mock_user

        result = await self.proxy.authenticate_token("valid_token")

        assert result is True
        assert self.proxy.username == "testuser"
        assert self.proxy.user_id == "user123"

    @pytest.mark.asyncio
    @patch("app.routers.ai_stream.jwt.decode")
    async def test_authenticate_token_failure(self, mock_info):
        mock_info.side_effect = JWTError("Invalid token")
        result = await self.proxy.authenticate_token("invalid")
        assert result is False

    @pytest.mark.asyncio
    async def test_handle_tool_call_get_todos(self):
        self.proxy.todos = [{"title": "Task 1", "priority": "high"}]
        fc = Mock()
        fc.name = "get_todos"

        result = await self.proxy._handle_tool_call(fc)

        assert "todos" in result
        assert result["todos"][0]["title"] == "Task 1"

    @pytest.mark.asyncio
    async def test_handle_tool_call_create_todo(self):
        fc = Mock()
        fc.name = "create_todo"
        fc.args = {"title": "New Task", "priority": "low"}

        result = await self.proxy._handle_tool_call(fc)

        assert result["status"] == "success"
        self.mock_ws.send_json.assert_called_with(
            {
                "type": "action",
                "action": "create_todo",
                "data": {
                    "title": "New Task",
                    "description": "",
                    "priority": "low",
                    "due_date": None,
                },
            }
        )

    @pytest.mark.asyncio
    @patch("app.routers.ai_stream.genai")
    @patch("app.routers.ai_stream.settings")
    async def test_start_connects_to_gemini(self, mock_settings, mock_genai):
        mock_settings.gemini_api_key = "test_key"

        # Mock Client and Session
        mock_client = Mock()
        mock_session = AsyncMock()

        # Mocking async context manager: client.aio.live.connect(...)
        # The .connect() call returns an object that has __aenter__ and __aexit__
        mock_connect_cm = AsyncMock()
        mock_connect_cm.__aenter__.return_value = mock_session
        mock_connect_cm.__aexit__.return_value = None

        mock_client.aio.live.connect.return_value = mock_connect_cm
        mock_genai.Client.return_value = mock_client

        # Mock websocket receive to break the loop (raise disconnect)
        self.mock_ws.receive_json.side_effect = WebSocketDisconnect()

        await self.proxy.start()

        mock_genai.Client.assert_called_with(api_key="test_key")
        mock_client.aio.live.connect.assert_called_once()
        # Should verify connected message
        self.mock_ws.send_json.assert_any_call({"type": "connected"})

    @pytest.mark.asyncio
    async def test_handle_tool_call_delete_todo(self):
        self.proxy.todos = [{"id": "1", "title": "Obsolete Task"}]
        fc = Mock()
        fc.name = "delete_todo"
        fc.args = {"search_title": "Obsolete"}

        result = await self.proxy._handle_tool_call(fc)

        assert result["status"] == "success"
        self.mock_ws.send_json.assert_called_with(
            {"type": "action", "action": "delete_todo", "data": {"id": "1"}}
        )

    @pytest.mark.asyncio
    async def test_handle_tool_call_update_todo(self):
        self.proxy.todos = [{"id": "1", "title": "Old Title", "priority": "low"}]
        fc = Mock()
        fc.name = "update_todo"
        fc.args = {"search_title": "Old", "new_priority": "high"}

        result = await self.proxy._handle_tool_call(fc)

        assert result["status"] == "success"
        assert "Updated task" in result["message"]
        self.mock_ws.send_json.assert_called_with(
            {
                "type": "action",
                "action": "update_todo",
                "data": {
                    "id": "1",
                    "title": "Old Title",
                    "description": None,
                    "priority": "high",
                    "due_date": None,
                },
            }
        )

    @pytest.mark.asyncio
    async def test_handle_tool_call_delete_todo_not_found(self):
        self.proxy.todos = []
        fc = Mock()
        fc.name = "delete_todo"
        fc.args = {"search_title": "NonExistent"}

        result = await self.proxy._handle_tool_call(fc)

        assert result["status"] == "error"
        assert "No task found" in result["message"]

    @pytest.mark.asyncio
    @patch("app.routers.ai_stream.settings")
    async def test_start_missing_api_key(self, mock_settings):
        mock_settings.gemini_api_key = None

        await self.proxy.start()

        self.mock_ws.send_json.assert_called_with(
            {
                "type": "error",
                "message": "AI service not configured",
            }
        )
        self.mock_ws.close.assert_called()

    @pytest.mark.asyncio
    async def test_handle_tool_call_multiple_matches(self):
        self.proxy.todos = [{"id": "1", "title": "Buy Milk"}, {"id": "2", "title": "Buy Miles"}]
        fc = Mock()
        fc.name = "delete_todo"
        fc.args = {"search_title": "Buy"}

        result = await self.proxy._handle_tool_call(fc)

        assert result["status"] == "error"
        assert "Multiple tasks found" in result["message"]

    @pytest.mark.asyncio
    async def test_handle_tool_call_exception(self):
        fc = Mock()
        fc.name = "unknown_tool"
        # Accessing args will not fail, but unknown name falls through?
        # No, unknown tool returns default error.
        # To trigger Exception in try/except block (lines 396-397), fail inside logic.
        # e.g. self.todos access fails?
        # Mock fc.name to be "get_todos" but make self.todos matching fail?
        # Or mock self.websocket.send_json to raise Exception during "create_todo" response.

        fc.name = "create_todo"
        fc.args = {"title": "Fail"}
        self.mock_ws.send_json.side_effect = Exception("Send failed")

        result = await self.proxy._handle_tool_call(fc)
        assert result["status"] == "error"
        assert "Send failed" in result["message"]

    @pytest.mark.asyncio
    async def test_stop_closes_session(self):
        self.proxy.gemini_session = AsyncMock()
        self.proxy._running = True

        await self.proxy.stop()

        assert self.proxy._running is False
        self.proxy.gemini_session.close.assert_awaited()

    @pytest.mark.asyncio
    async def test_forward_client_to_gemini_error(self):
        self.proxy._running = True
        # Mock receive_json to raise Exception immediately
        self.mock_ws.receive_json.side_effect = Exception("Connection error")

        await self.proxy._forward_client_to_gemini()

        assert self.proxy._running is False

    @pytest.mark.asyncio
    @patch("app.routers.ai_stream.settings")
    async def test_start_exception(self, mock_settings):
        mock_settings.gemini_api_key = "key"
        # Mock genai.Client to raise Exception
        with patch("app.routers.ai_stream.genai.Client", side_effect=Exception("API Error")):
            await self.proxy.start()

        self.mock_ws.send_json.assert_called_with(
            {
                "type": "error",
                "message": "Failed to connect to AI service: API Error",
            }
        )
        self.mock_ws.close.assert_called()

    @pytest.mark.asyncio
    @patch("app.routers.ai_stream.jwt.decode")
    async def test_authenticate_token_no_username(self, mock_decode):
        """Test authentication when token has no username."""
        mock_decode.return_value = {}  #  No "sub" key - line 40
        result = await self.proxy.authenticate_token("token")
        assert result is False

    @pytest.mark.asyncio
    @patch("app.routers.ai_stream.jwt.decode")
    @patch("app.routers.ai_stream.get_user_by_username")
    async def test_authenticate_token_user_not_found(self, mock_get_user, mock_decode):
        """Test authentication when user doesn't exist in database."""
        mock_decode.return_value = {"sub": "nonexistent"}
        mock_get_user.return_value = None  # Line 43
        result = await self.proxy.authenticate_token("token")
        assert result is False

    @pytest.mark.asyncio
    async def test_forward_client_audio_messages(self):
        """Test forwarding audio chunks from client to Gemini."""
        self.proxy._running = True
        self.proxy.gemini_session = AsyncMock()

        # Simulate audio message followed by disconnect
        self.mock_ws.receive_json.side_effect = [
            {"type": "audio", "data": "base64data"},
            WebSocketDisconnect(),
        ]

        await self.proxy._forward_client_to_gemini()

        # Should have sent audio to Gemini
        self.proxy.gemini_session.send.assert_called_once()
        assert self.proxy._running is False

    @pytest.mark.asyncio
    async def test_forward_client_end_turn(self):
        """Test forwarding end_turn signal from client to Gemini."""
        self.proxy._running = True
        self.proxy.gemini_session = AsyncMock()

        self.mock_ws.receive_json.side_effect = [
            {"type": "end_turn"},
            WebSocketDisconnect(),
        ]

        await self.proxy._forward_client_to_gemini()

        # Should send end_of_turn=True to Gemini
        self.proxy.gemini_session.send.assert_called_with(input=None, end_of_turn=True)

    @pytest.mark.asyncio
    async def test_forward_client_todos_update(self):
        """Test receiving todos update from client."""
        self.proxy._running = True
        self.proxy.gemini_session = AsyncMock()

        todos = [{"id": "1", "title": "Test"}]
        self.mock_ws.receive_json.side_effect = [
            {"type": "todos_update", "todos": todos},
            WebSocketDisconnect(),
        ]

        await self.proxy._forward_client_to_gemini()

        assert self.proxy.todos == todos


class TestVoiceStreamEndpointDirect:
    allowed_headers = {"origin": "http://localhost:3000"}

    @pytest.mark.asyncio
    @patch("app.routers.ai_stream.GeminiLiveProxy")
    async def test_endpoint_success_flow(self, mock_proxy_cls):
        mock_ws = AsyncMock(spec=WebSocket)
        mock_ws.cookies = {}
        mock_ws.headers = self.allowed_headers
        mock_ws.receive_json.return_value = {"type": "auth", "token": "valid"}
        mock_proxy_inst = AsyncMock()
        mock_proxy_inst.authenticate_token.return_value = True
        mock_proxy_inst.username = "testuser"
        mock_proxy_cls.return_value = mock_proxy_inst

        # Test normal flow: Connect -> Auth -> Start -> Stop
        # To avoid infinite loop or hang, mock start/stop effectively
        await voice_stream(mock_ws)

        mock_ws.accept.assert_awaited()
        mock_ws.receive_json.assert_awaited()
        mock_proxy_cls.assert_called_with(mock_ws, "", "")
        mock_proxy_inst.authenticate_token.assert_awaited_with("valid")
        mock_proxy_inst.start.assert_awaited()
        mock_proxy_inst.stop.assert_awaited()

    @pytest.mark.asyncio
    @patch("app.routers.ai_stream.GeminiLiveProxy")
    async def test_endpoint_success_flow_cookies(self, mock_proxy_cls):
        mock_ws = AsyncMock(spec=WebSocket)
        mock_ws.cookies = {"access_token": "valid_cookie_token"}
        mock_ws.headers = self.allowed_headers

        mock_proxy_inst = AsyncMock()
        mock_proxy_inst.authenticate_token.return_value = True
        mock_proxy_inst.username = "testuser"
        mock_proxy_cls.return_value = mock_proxy_inst

        await voice_stream(mock_ws)

        mock_ws.accept.assert_awaited()
        # Should NOT await receive_json because cookie was present
        mock_ws.receive_json.assert_not_awaited()
        mock_proxy_cls.assert_called_with(mock_ws, "", "")
        mock_proxy_inst.authenticate_token.assert_awaited_with("valid_cookie_token")
        mock_proxy_inst.start.assert_awaited()
        mock_proxy_inst.stop.assert_awaited()

    @pytest.mark.asyncio
    async def test_endpoint_no_auth(self):
        mock_ws = AsyncMock(spec=WebSocket)
        mock_ws.headers = self.allowed_headers
        mock_ws.receive_json.return_value = {"type": "other"}

        await voice_stream(mock_ws)

        mock_ws.send_json.assert_called_with(
            {"type": "error", "message": "First message must be auth"}
        )
        mock_ws.close.assert_awaited()

    @pytest.mark.asyncio
    async def test_endpoint_invalid_token(self):
        mock_ws = AsyncMock(spec=WebSocket)
        mock_ws.headers = self.allowed_headers
        mock_ws.receive_json.return_value = {"type": "auth", "token": "bad"}

        # Mock Proxy to return specific instance that fails auth
        with patch("app.routers.ai_stream.GeminiLiveProxy") as mock_cls:
            mock_inst = AsyncMock()
            mock_inst.authenticate_token.return_value = False
            mock_cls.return_value = mock_inst

            await voice_stream(mock_ws)

            mock_ws.send_json.assert_called_with({"type": "error", "message": "Invalid token"})
            mock_ws.close.assert_awaited()

    @pytest.mark.asyncio
    async def test_endpoint_timeout(self):
        mock_ws = AsyncMock(spec=WebSocket)
        mock_ws.headers = self.allowed_headers
        mock_ws.receive_json.side_effect = TimeoutError()

        await voice_stream(mock_ws)

        mock_ws.send_json.assert_called_with({"type": "error", "message": "Authentication timeout"})
        mock_ws.close.assert_awaited()

    @pytest.mark.asyncio
    async def test_endpoint_generic_exception(self):
        mock_ws = AsyncMock(spec=WebSocket)
        mock_ws.headers = self.allowed_headers
        mock_ws.receive_json.side_effect = Exception("Boom")

        await voice_stream(mock_ws)

        mock_ws.close.assert_awaited()

    @pytest.mark.asyncio
    async def test_endpoint_disconnect_during_start(self):
        mock_ws = AsyncMock(spec=WebSocket)
        mock_ws.headers = self.allowed_headers
        mock_ws.receive_json.return_value = {"type": "auth", "token": "valid"}

        with patch("app.routers.ai_stream.GeminiLiveProxy") as mock_cls:
            mock_inst = AsyncMock()
            mock_inst.username = "user"
            mock_inst.authenticate_token.return_value = True
            mock_inst.start.side_effect = WebSocketDisconnect()
            mock_cls.return_value = mock_inst

            await voice_stream(mock_ws)
            # Should log and exit gracefully, not raise
            mock_inst.stop.assert_awaited()

    @pytest.mark.asyncio
    async def test_endpoint_rejects_missing_origin(self):
        mock_ws = AsyncMock(spec=WebSocket)
        mock_ws.headers = {}

        await voice_stream(mock_ws)

        mock_ws.accept.assert_not_awaited()
        mock_ws.close.assert_awaited_with(code=1008)
