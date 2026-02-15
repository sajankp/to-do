from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException
from jose import JWTError, jwt

from app.models.user import UserInDB
from app.routers.auth import (
    PASSWORD_ALGORITHM,
    SECRET_KEY,
    authenticate_user,
    create_jwt_token,
    create_token,
    get_authenticated_user,
    get_user_info_from_token,
    hash_password,
    verify_password,
)
from app.utils.constants import INVALID_TOKEN
from app.utils.jwt import decode_jwt_token


class TestDecodeJWTToken:
    @patch("jose.jwt.decode")
    def test_valid_token_decodes_successfully(self, mock_decode):
        mock_payload = {
            "sub": "test_user",
            "exp": datetime.now() + timedelta(minutes=30),
        }
        mock_token = "valid.jwt.token"
        mock_decode.return_value = mock_payload

        result = decode_jwt_token(mock_token)

        mock_decode.assert_called_once_with(mock_token, SECRET_KEY, algorithms=[PASSWORD_ALGORITHM])
        assert result == mock_payload, "Expected payload does not match the result."

    @patch("jose.jwt.decode")
    def test_valid_token_returns_user_info(self, mock_decode):
        test_username = "test_user"
        test_user_id = "123"
        test_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9"
        mock_decode.return_value = {"sub": test_username, "sub_id": test_user_id}

        username, user_id = get_user_info_from_token(test_token)

        mock_decode.assert_called_once_with(test_token, SECRET_KEY, algorithms=[PASSWORD_ALGORITHM])
        assert username == test_username, "Username does not match expected value."
        assert user_id == test_user_id, "User ID does not match expected value."

    @patch("jose.jwt.decode")
    def test_missing_sub_raises_exception(self, mock_decode):
        test_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9"
        mock_decode.return_value = {"sub": None, "sub_id": "123"}

        with pytest.raises(HTTPException) as exc_info:
            get_user_info_from_token(test_token)

        assert exc_info.value.status_code == 401, "Expected HTTP 401 Unauthorized."
        assert exc_info.value.detail == INVALID_TOKEN, "Detail message does not match."
        assert exc_info.value.headers == {
            "WWW-Authenticate": "Bearer"
        }, "Expected WWW-Authenticate header in the exception."


class TestTokenExceptions:
    def test_invalid_token(self):
        test_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9"

        with pytest.raises(HTTPException) as exc_info:
            get_user_info_from_token(test_token)

        assert exc_info.value.detail.startswith(
            "JWTError"
        ), "Expected detail to start with 'JWTError'."

    def test_expired_token(self):
        test_token = create_token(
            data={"sub": "test", "sub_id": "123"},
            expires_delta=timedelta(minutes=-30),
        )

        with pytest.raises(HTTPException) as exc_info:
            get_user_info_from_token(test_token)

        assert (
            exc_info.value.detail == "Token has expired"
        ), "Expected detail to indicate the token has expired."


# Mock constants
MOCK_SECRET_KEY = "mock_secret"
MOCK_ALGORITHM = "HS256"


@patch("jose.jwt.encode")
def test_create_jwt_token(mock_encode):
    mock_data = {"sub": "test_user"}
    mock_encoded_token = "mock.encoded.jwt"
    mock_encode.return_value = mock_encoded_token

    token = create_jwt_token(mock_data)

    mock_encode.assert_called_once_with(mock_data, SECRET_KEY, algorithm=PASSWORD_ALGORITHM)
    assert token == mock_encoded_token


@patch("jose.jwt.decode")
def test_decode_jwt_token(mock_decode):
    mock_token = "mock.jwt.token"
    mock_payload = {"sub": "test_user"}
    mock_decode.return_value = mock_payload

    payload = decode_jwt_token(mock_token)

    mock_decode.assert_called_once_with(mock_token, SECRET_KEY, algorithms=[PASSWORD_ALGORITHM])
    assert payload == mock_payload


@patch("jose.jwt.decode")
def test_decode_jwt_token_invalid(mock_decode):
    mock_token = "invalid.jwt.token"
    mock_decode.side_effect = JWTError

    payload = decode_jwt_token(mock_token)

    assert payload is None


def test_create_token():
    data = {"sub": "test_user"}
    expires_delta = timedelta(minutes=30)
    token = create_token(data, expires_delta)

    payload = jwt.decode(token, SECRET_KEY, algorithms=[PASSWORD_ALGORITHM])
    assert payload["sub"] == "test_user"
    assert payload["exp"] > datetime.now().timestamp()


def test_create_token_without_expiry():
    data = {"sub": "test_user"}
    token = create_token(data)

    payload = jwt.decode(token, SECRET_KEY, algorithms=[PASSWORD_ALGORITHM])
    assert payload["sub"] == "test_user"
    assert payload["exp"] > datetime.now().timestamp()


### Tests for `password`-related functions


@patch("app.routers.auth.pwd_hash.hash")
def test_hash_password(mock_hash):
    mock_hash.return_value = "hashed_password"
    password = "plain_password"

    hashed_password = hash_password(password)

    mock_hash.assert_called_once_with(password)
    assert hashed_password == "hashed_password"


@patch("app.routers.auth.pwd_hash.verify_and_update")
def test_verify_password(mock_verify_and_update):
    mock_verify_and_update.return_value = (True, None)
    plain_password = "plain_password"
    hashed_password = "hashed_password"

    is_valid, new_hash = verify_password(plain_password, hashed_password)

    mock_verify_and_update.assert_called_once_with(plain_password, hashed_password)
    assert is_valid is True
    assert new_hash is None


### Tests for user-related functions


@patch("app.routers.auth.get_user_by_username")
@patch("app.routers.auth.verify_password")
def test_authenticate_user(mock_verify_password, mock_get_user, mock_mongo_client):
    mock_user = UserInDB(
        username="test_user",
        hashed_password="hashed_password",
        email="email@example.com",
    )
    mock_get_user.return_value = mock_user
    mock_verify_password.return_value = (True, None)

    user, new_hash = authenticate_user("test_user", "plain_password", mock_mongo_client)

    mock_get_user.assert_called_once_with("test_user", mock_mongo_client)
    mock_verify_password.assert_called_once_with("plain_password", "hashed_password")
    assert isinstance(user, UserInDB)
    assert user.username == "test_user"
    assert new_hash is None


@patch("app.routers.auth.get_user_by_username")
def test_authenticate_user_invalid(mock_get_user, mock_mongo_client):
    mock_get_user.return_value = None

    user, new_hash = authenticate_user("invalid_user", "plain_password", mock_mongo_client)

    mock_get_user.assert_called_once_with("invalid_user", mock_mongo_client)
    assert user is None
    assert new_hash is None


class TestGetAuthenticatedUser:
    @patch("app.routers.auth.get_user_by_username")
    def test_valid_state_returns_user(self, mock_get_user, mock_mongo_client):
        # Mock Request and State
        mock_request = Mock()
        mock_request.state.user_id = "507f1f77bcf86cd799439011"
        mock_request.state.username = "test_user"
        mock_request.app.mongodb_client = mock_mongo_client

        # Mock User DB response
        mock_user = UserInDB(
            username="test_user",
            hashed_password="hashed_password",
            email="email@example.com",
        )
        mock_get_user.return_value = mock_user

        user = get_authenticated_user(mock_request)

        mock_get_user.assert_called_once_with("test_user", mock_mongo_client)
        assert isinstance(user, UserInDB)
        assert user.username == mock_user.username

    def test_missing_state_raises_exception(self):
        # Mock Request with missing state
        mock_request = Mock()
        # Ensure 'user_id' attribute raises AttributeError or is falsy
        del mock_request.state.user_id

        # Alternatively, strictly mock state as an object that doesn't have user_id
        # But Mock creates attributes on access.
        # Better:
        mock_request = Mock()
        mock_request.state = Mock(spec=[])  # Empty object

        with pytest.raises(HTTPException) as exc_info:
            get_authenticated_user(mock_request)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Not authenticated"

    @patch("app.routers.auth.get_user_by_username")
    def test_user_not_found_raises_exception(self, mock_get_user, mock_mongo_client):
        # Mock Request

        mock_request = Mock()
        mock_request.state.user_id = "507f1f77bcf86cd799439011"
        mock_request.state.username = "test_user"
        mock_request.app.mongodb_client = mock_mongo_client

        # Mock User not found
        mock_get_user.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_authenticated_user(mock_request)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "User not found"


@patch("app.routers.auth.get_user_by_username")
@patch("app.routers.auth.verify_password")
def test_authenticate_user_wrong_password(mock_verify_password, mock_get_user, mock_mongo_client):
    mock_user = UserInDB(
        username="test_user",
        hashed_password="hashed_password",
        email="email@example.com",
    )
    mock_get_user.return_value = mock_user
    mock_verify_password.return_value = (False, None)  # Simulate wrong password

    user, new_hash = authenticate_user("test_user", "wrong_password", mock_mongo_client)

    mock_get_user.assert_called_once_with("test_user", mock_mongo_client)
    mock_verify_password.assert_called_once_with("wrong_password", "hashed_password")
    assert user is None, "authenticate_user should return None on wrong password"
    assert new_hash is None
