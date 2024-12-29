from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.routers.auth import (
    PASSWORD_ALGORITHM,
    SECRET_KEY,
    create_token,
    decode_jwt_token,
    get_user_info_from_token,
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
