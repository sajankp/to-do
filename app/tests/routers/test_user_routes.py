from datetime import UTC, datetime
from unittest.mock import Mock, patch

import pymongo.errors
from bson import ObjectId


def test_create_user_success(client, mock_mongo_client):
    # Mock the user collection on the app instance
    # app.user is already patched by the autouse fixture 'patch_mongo_client'
    # We just need to configure the return values of the mock
    mock_insert = Mock(acknowledged=True)
    mock_mongo_client["test_db"]["users"].insert_one.return_value = mock_insert

    # client = TestClient(app) <-- Removed

    response = client.post(
        "/user",
        json={"username": "newuser", "email": "new@example.com", "password": "password123"},
    )

    assert response.status_code == 200
    assert response.json() is True

    # Verify call args
    # Verify call args
    args = mock_mongo_client["test_db"]["users"].insert_one.call_args[0][0]
    assert args["username"] == "newuser"
    assert args["email"] == "new@example.com"
    assert args["hashed_password"] != "password123"  # Should be hashed


def test_create_user_validation_error(client):
    # client = TestClient(app) <-- Removed

    response = client.post(
        "/user",
        json={
            "username": "newuser",
            # Missing email and password
        },
    )

    assert response.status_code == 422


def test_create_user_duplicate(client, mock_mongo_client):
    # Mock the user collection and simulation DuplicateKeyError
    # app.user is already patched by the autouse fixture 'patch_mongo_client'
    mock_mongo_client["test_db"]["users"].insert_one.side_effect = pymongo.errors.DuplicateKeyError(
        "duplicate"
    )

    # client = TestClient(app) <-- Removed

    response = client.post(
        "/user",
        json={"username": "existing", "email": "exists@example.com", "password": "password123"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Username or email already exists"

    # Verify duplicate user handling


@patch("app.main.get_user_info_from_token")
def test_read_users_me_success(mock_get_user_info, client, mock_mongo_client):  # Added client
    # Mock token decoding
    user_id_str = "507f1f77bcf86cd799439011"
    mock_get_user_info.return_value = ("testuser", user_id_str)

    # Mock DB finding the user
    # app.user and app.mongodb_client are patched by autouse fixture
    mock_user = {
        "_id": ObjectId(user_id_str),
        "username": "testuser",
        "email": "test@example.com",
        "hashed_password": "hashed",
        "disabled": False,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    mock_mongo_client["test_db"]["users"].find_one.return_value = mock_user

    # client = TestClient(app) <-- Removed

    # Make request with cookie
    response = client.get("/user/me", cookies={"access_token": "valid_token"})

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    mock_mongo_client["test_db"]["users"].find_one.assert_called_once()
