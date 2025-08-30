from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from jose import JWTError, jwt

from app.models.user import User
from app.routers.auth import (
    PASSWORD_ALGORITHM,
    SECRET_KEY,
    authenticate_user,
    create_jwt_token,
    create_token,
    decode_jwt_token,
    get_current_active_user,
    get_user_info_from_token,
    hash_password,
    verify_password,
)
from app.utils.constants import INVALID_TOKEN


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

        mock_decode.assert_called_once_with(
            mock_token, SECRET_KEY, algorithms=[PASSWORD_ALGORITHM]
        )
        assert result == mock_payload, "Expected payload does not match the result."

    @patch("jose.jwt.decode")
    def test_valid_token_returns_user_info(self, mock_decode):
        test_username = "test_user"
        test_user_id = "123"
        test_token = "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9"
        mock_decode.return_value = {"sub": test_username, "sub_id": test_user_id}

        username, user_id = get_user_info_from_token(test_token)

        mock_decode.assert_called_once_with(
            test_token.split(" ")[1], SECRET_KEY, algorithms=[PASSWORD_ALGORITHM]
        )
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

    mock_encode.assert_called_once_with(
        mock_data, SECRET_KEY, algorithm=PASSWORD_ALGORITHM
    )
    assert token == mock_encoded_token


@patch("jose.jwt.decode")
def test_decode_jwt_token(mock_decode):
    mock_token = "mock.jwt.token"
    mock_payload = {"sub": "test_user"}
    mock_decode.return_value = mock_payload

    payload = decode_jwt_token(mock_token)

    mock_decode.assert_called_once_with(
        mock_token, SECRET_KEY, algorithms=[PASSWORD_ALGORITHM]
    )
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


@patch("app.routers.auth.pwd_context.hash")
def test_hash_password(mock_hash):
    mock_hash.return_value = "hashed_password"
    password = "plain_password"

    hashed_password = hash_password(password)

    mock_hash.assert_called_once_with(password)
    assert hashed_password == "hashed_password"


@patch("app.routers.auth.pwd_context.verify")
def test_verify_password(mock_verify):
    mock_verify.return_value = True
    plain_password = "plain_password"
    hashed_password = "hashed_password"

    is_valid = verify_password(plain_password, hashed_password)

    mock_verify.assert_called_once_with(plain_password, hashed_password)
    assert is_valid is True


### Tests for user-related functions


@patch("app.routers.auth.get_user_by_username")
@patch("app.routers.auth.verify_password")
def test_authenticate_user(mock_verify_password, mock_get_user):
    mock_user = {
        "username": "test_user",
        "hashed_password": "hashed_password",
        "email": "email",
    }
    mock_get_user.return_value = mock_user
    mock_verify_password.return_value = True

    user = authenticate_user("test_user", "plain_password")

    mock_get_user.assert_called_once_with("test_user")
    mock_verify_password.assert_called_once_with("plain_password", "hashed_password")
    assert isinstance(user, User)
    assert user.username == "test_user", "Expected username to match 'test_user'."


@patch("app.routers.auth.get_user_by_username")
def test_authenticate_user_invalid(mock_get_user):
    mock_get_user.return_value = None

    user = authenticate_user("invalid_user", "plain_password")

    mock_get_user.assert_called_once_with("invalid_user")
    assert user is None


class TestGetCurrentActiveUser:
    @patch("app.routers.auth.get_user_by_username")
    @patch("jose.jwt.decode")
    def test_valid_token_returns_user(self, mock_decode, mock_get_user):
        mock_user = {
            "username": "test_user",
            "hashed_password": "hashed_password",
            "email": "email@example.com",
        }
        mock_get_user.return_value = mock_user
        mock_decode.return_value = {"sub": "test_user"}
        mock_token = "mock.jwt.token"

        user = get_current_active_user(mock_token)

        mock_decode.assert_called_once_with(
            mock_token, SECRET_KEY, algorithms=[PASSWORD_ALGORITHM]
        )
        mock_get_user.assert_called_once_with("test_user")
        assert isinstance(user, User)
        assert user.username == mock_user["username"]

    @patch("app.routers.auth.get_user_by_username")
    @patch("jose.jwt.decode")
    def test_missing_username_raises_exception(self, mock_decode, mock_get_user):
        mock_decode.return_value = {"sub": None}
        mock_get_user.return_value = None
        mock_token = "mock.jwt.token"
        credentials_exception = HTTPException(
            status_code=401,
            detail=INVALID_TOKEN,
            headers={"WWW-Authenticate": "Bearer"},
        )

        with pytest.raises(HTTPException) as exc_info:
            get_current_active_user(mock_token)

        mock_decode.assert_called_once_with(
            mock_token, SECRET_KEY, algorithms=[PASSWORD_ALGORITHM]
        )
        assert exc_info.value.status_code == credentials_exception.status_code
        assert exc_info.value.detail == credentials_exception.detail

    @patch("app.routers.auth.get_user_by_username")
    @patch("jose.jwt.decode")
    def test_invalid_token_raises_exception(self, mock_decode, mock_get_user):
        mock_decode.side_effect = JWTError
        mock_get_user.return_value = None
        mock_token = "mock.jwt.token"
        credentials_exception = HTTPException(
            status_code=401,
            detail=INVALID_TOKEN,
            headers={"WWW-Authenticate": "Bearer"},
        )

        with pytest.raises(HTTPException) as exc_info:
            get_current_active_user(mock_token)

        mock_decode.assert_called_once_with(
            mock_token, SECRET_KEY, algorithms=[PASSWORD_ALGORITHM]
        )
        assert exc_info.value.status_code == credentials_exception.status_code
        assert exc_info.value.detail == credentials_exception.detail

    @patch("app.routers.auth.get_user_by_username")
    @patch("jose.jwt.decode")
    def test_user_not_found_raises_exception(self, mock_decode, mock_get_user):
        mock_decode.return_value = {"sub": "nonexistent_user"}
        mock_get_user.return_value = None
        mock_token = "mock.jwt.token"
        credentials_exception = HTTPException(
            status_code=401,
            detail=INVALID_TOKEN,
            headers={"WWW-Authenticate": "Bearer"},
        )

        with pytest.raises(HTTPException) as exc_info:
            get_current_active_user(mock_token)

        mock_decode.assert_called_once_with(
            mock_token, SECRET_KEY, algorithms=[PASSWORD_ALGORITHM]
        )
        mock_get_user.assert_called_once_with("nonexistent_user")
        assert exc_info.value.status_code == credentials_exception.status_code
        assert exc_info.value.detail == credentials_exception.detail


@patch("app.routers.auth.get_user_by_username")
@patch("app.routers.auth.verify_password")
def test_authenticate_user_wrong_password(mock_verify_password, mock_get_user):
    mock_user = {
        "username": "test_user",
        "hashed_password": "hashed_password",
        "email": "email",
    }
    mock_get_user.return_value = mock_user
    mock_verify_password.return_value = False  # Simulate wrong password

    user = authenticate_user("test_user", "wrong_password")

    mock_get_user.assert_called_once_with("test_user")
    mock_verify_password.assert_called_once_with("wrong_password", "hashed_password")
    assert user is None, "authenticate_user should return None on wrong password"
