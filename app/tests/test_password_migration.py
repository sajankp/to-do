"""Tests for transparent password hash migration in /token endpoint."""

from unittest.mock import Mock, patch

import pymongo.errors
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_app():
    """Mock app attributes that are usually set in lifespan."""
    app.mongodb_client = Mock()
    app.user = Mock()
    app.todo = Mock()
    app.settings = Mock()
    yield


class TestPasswordHashMigration:
    """Tests for transparent hash migration from bcrypt to Argon2id."""

    @patch("app.main.authenticate_user")
    @patch("app.main.create_token")
    def test_hash_migration_on_successful_login(self, mock_create_token, mock_authenticate_user):
        """Test that old bcrypt hashes are upgraded to Argon2id on login."""
        # Setup: user with old bcrypt hash logs in
        mock_user = Mock()
        mock_user.username = "testuser"
        mock_user.id = "507f1f77bcf86cd799439011"
        new_argon2_hash = "$argon2id$v=19$m=65536,t=3,p=4$..."

        # authenticate_user returns (user, new_hash) when migration needed
        mock_authenticate_user.return_value = (mock_user, new_argon2_hash)
        mock_create_token.return_value = "fake_token"

        # Make login request
        response = client.post(
            "/token",
            data={"username": "testuser", "password": "password123"},
            headers={"X-Forwarded-For": "127.0.0.1"},
        )

        # Verify successful login
        assert response.status_code == 200
        assert "access_token" in response.json()

        # Verify hash was upgraded in database
        app.user.update_one.assert_called_once_with(
            {"username": "testuser"}, {"$set": {"hashed_password": new_argon2_hash}}
        )

    @patch("app.main.authenticate_user")
    @patch("app.main.create_token")
    def test_no_migration_when_hash_is_current(self, mock_create_token, mock_authenticate_user):
        """Test that no DB update occurs when hash is already Argon2id."""
        mock_user = Mock()
        mock_user.username = "testuser"
        mock_user.id = "507f1f77bcf86cd799439011"

        # authenticate_user returns (user, None) when no migration needed
        mock_authenticate_user.return_value = (mock_user, None)
        mock_create_token.return_value = "fake_token"

        response = client.post(
            "/token",
            data={"username": "testuser", "password": "password123"},
            headers={"X-Forwarded-For": "127.0.0.1"},
        )

        assert response.status_code == 200

        # Verify NO database update was attempted
        app.user.update_one.assert_not_called()

    @patch("app.main.authenticate_user")
    @patch("app.main.create_token")
    @patch("app.main.logging")
    def test_migration_failure_does_not_block_login(
        self, mock_logging, mock_create_token, mock_authenticate_user
    ):
        """Test that DB update failures don't prevent successful login."""
        mock_user = Mock()
        mock_user.username = "testuser"
        mock_user.id = "507f1f77bcf86cd799439011"
        new_hash = "$argon2id$v=19$m=65536,t=3,p=4$..."

        mock_authenticate_user.return_value = (mock_user, new_hash)
        mock_create_token.return_value = "fake_token"

        # Simulate DB failure during hash update
        app.user.update_one.side_effect = pymongo.errors.PyMongoError("DB connection lost")

        response = client.post(
            "/token",
            data={"username": "testuser", "password": "password123"},
            headers={"X-Forwarded-For": "127.0.0.1"},
        )

        # Login should still succeed despite DB error
        assert response.status_code == 200
        assert "access_token" in response.json()

        # Verify warning was logged
        mock_logging.warning.assert_called_once()
        assert "Failed to upgrade password hash" in str(mock_logging.warning.call_args)
        assert "testuser" in str(mock_logging.warning.call_args)
