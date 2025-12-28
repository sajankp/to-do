from unittest.mock import Mock

from fastapi.testclient import TestClient

from app.main import app


def test_create_user_success():
    # Mock the user collection on the app instance
    app.user = Mock()
    mock_insert = Mock(acknowledged=True)
    app.user.insert_one = Mock(return_value=mock_insert)

    client = TestClient(app)

    response = client.post(
        "/user",
        json={"username": "newuser", "email": "new@example.com", "password": "password123"},
    )

    assert response.status_code == 200
    assert response.json() is True

    # Verify call args
    args = app.user.insert_one.call_args[0][0]
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
