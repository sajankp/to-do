from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from app.main import app


def test_create_user_success():
    client = TestClient(app)

    # Mock the database insert
    with patch("app.main.app.user.insert_one") as mock_insert:
        mock_insert.return_value = Mock(acknowledged=True)

        response = client.post(
            "/user",
            json={"username": "newuser", "email": "new@example.com", "password": "password123"},
        )

        assert response.status_code == 200
        assert response.json() is True

        # Verify call args
        args = mock_insert.call_args[0][0]
        assert args["username"] == "newuser"
        assert args["email"] == "new@example.com"
        assert args["hashed_password"] != "password123"  # Should be hashed


def test_create_user_validation_error():
    client = TestClient(app)

    response = client.post(
        "/user",
        json={
            "username": "newuser",
            # Missing email and password
        },
    )

    assert response.status_code == 422
