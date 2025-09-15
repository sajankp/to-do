from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest
from pymongo.errors import ServerSelectionTimeoutError

from app.utils.health import app_check_health, check_app_readiness


class TestHealthModule:

    @pytest.mark.asyncio
    @patch("app.utils.health.get_mongo_client")
    async def test_check_app_readiness_succeeds_on_first_attempt(self, mock_get_client):
        mock_get_client.return_value.admin.command.return_value = {"ok": 1}
        result = await check_app_readiness(max_attempts=1)
        assert result is True
        mock_get_client.return_value.admin.command.assert_called_once_with("ping", 1)

    @pytest.mark.asyncio
    @patch("asyncio.sleep", new_callable=AsyncMock)
    @patch("app.utils.health.get_mongo_client")
    async def test_check_app_readiness_retries_on_failure(
        self, mock_get_client, mock_sleep
    ):
        # First call raises, second succeeds
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.admin.command.side_effect = [
            ServerSelectionTimeoutError("Failed"),
            {"ok": 1},
        ]

        result = await check_app_readiness(max_attempts=2, timeout=0.1)

        assert result is True
        assert mock_client.admin.command.call_count == 2
        mock_sleep.assert_called_once_with(0.1)

    @pytest.mark.asyncio
    @patch("asyncio.sleep", new_callable=AsyncMock)
    @patch("app.utils.health.get_mongo_client")
    async def test_check_app_readiness_fails_after_max_attempts(
        self, mock_client, mock_sleep
    ):
        mock_client.return_value.admin.command.side_effect = (
            ServerSelectionTimeoutError("Failed")
        )
        result = await check_app_readiness(max_attempts=3, timeout=0.1)
        assert result is False
        assert mock_client.return_value.admin.command.call_count == 3
        assert mock_sleep.call_count == 3

    @pytest.mark.asyncio
    @patch("app.utils.health.get_mongo_client")
    async def test_check_app_readiness_uses_correct_timeout(self, mock_client):
        mock_client.return_value.admin.command.return_value = {"ok": 1}

        await check_app_readiness(timeout=2.5)

        mock_client.return_value.admin.command.assert_called_once_with("ping", 2.5)

    def test_app_check_health_handles_none_client(self):
        app = SimpleNamespace(mongodb_client=None)
        result = app_check_health(app)
        assert result["status"] == "Error"
        assert "NoneType" in result["error"]

    def test_app_check_health_with_invalid_admin_object(self):
        mock_client = Mock()
        mock_client.admin = None
        app = SimpleNamespace(mongodb_client=mock_client)

        result = app_check_health(app)

        assert result["status"] == "Error"
        assert "NoneType" in result["error"]

    def test_app_check_health_with_network_timeout(self):
        command_mock = Mock(side_effect=ServerSelectionTimeoutError("Network timeout"))
        admin_mock = Mock()
        admin_mock.command = command_mock
        mongodb_client_mock = Mock()
        mongodb_client_mock.admin = admin_mock
        app = SimpleNamespace(mongodb_client=mongodb_client_mock)

        result = app_check_health(app)

        assert result["status"] == "Error"
        assert "Network timeout" in result["error"]


class TestAppCheckHealth:
    def test_returns_ok_when_ping_succeeds(
        self,
    ):
        command_mock = Mock(return_value={"ok": 1})
        admin_mock = Mock()
        admin_mock.command = command_mock
        mongodb_client_mock = Mock()
        mongodb_client_mock.admin = admin_mock
        app_obj = SimpleNamespace(mongodb_client=mongodb_client_mock)

        result = app_check_health(app_obj)

        assert result == {"status": "OK"}

    def test_invokes_ping_once_on_admin(
        self,
    ):
        command_mock = Mock(return_value={"ok": 1})
        admin_mock = Mock()
        admin_mock.command = command_mock
        mongodb_client_mock = Mock()
        mongodb_client_mock.admin = admin_mock
        app_obj = SimpleNamespace(mongodb_client=mongodb_client_mock)

        app_check_health(app_obj)

        command_mock.assert_called_once_with("ping")

    def test_returns_ok_even_if_ping_returns_none(
        self,
    ):
        command_mock = Mock(return_value=None)
        admin_mock = Mock()
        admin_mock.command = command_mock
        mongodb_client_mock = Mock()
        mongodb_client_mock.admin = admin_mock
        app_obj = SimpleNamespace(mongodb_client=mongodb_client_mock)

        result = app_check_health(app_obj)

        assert result == {"status": "OK"}

    def test_returns_error_when_client_missing(self):
        app_obj = SimpleNamespace()  # no mongodb_client attribute

        result = app_check_health(app_obj)

        assert result == {"status": "Error", "error": "MongoDB client not initialized"}

    def test_returns_error_with_exception_message_on_ping_failure(
        self,
    ):
        command_mock = Mock(side_effect=Exception("boom"))
        admin_mock = Mock()
        admin_mock.command = command_mock
        mongodb_client_mock = Mock()
        mongodb_client_mock.admin = admin_mock
        app_obj = SimpleNamespace(mongodb_client=mongodb_client_mock)

        result = app_check_health(app_obj)

        assert result["status"] == "Error"
        assert result["error"] == "boom"

    def test_returns_error_when_client_is_malformed(self):
        class AppLike:
            pass

        app_obj = AppLike()
        app_obj.mongodb_client = None  # malformed: missing 'admin'

        result = app_check_health(app_obj)

        assert result["status"] == "Error"
        assert "admin" in result["error"]
