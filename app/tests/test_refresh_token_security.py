from datetime import timedelta
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException, Response

from app.main import refresh_token
from app.routers.auth import create_token


def _mock_request_with_refresh_cookie(token: str) -> Mock:
    request = Mock()
    request.cookies = {"refresh_token": token}
    request.app.mongodb_client = Mock()
    return request


def test_refresh_rejects_access_token_in_cookie():
    access_token = create_token(
        data={"sub": "test_user", "sub_id": "507f1f77bcf86cd799439011"},
        expires_delta=timedelta(minutes=10),
        sid="session-id",
        token_type="access",
    )
    request = _mock_request_with_refresh_cookie(access_token)
    response = Response()

    with pytest.raises(HTTPException) as exc_info:
        refresh_token(request, response)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid refresh token"


@patch("app.main.get_user_by_username")
def test_refresh_accepts_refresh_token_type(mock_get_user):
    refresh_jwt = create_token(
        data={"sub": "test_user", "sub_id": "507f1f77bcf86cd799439011"},
        expires_delta=timedelta(minutes=10),
        sid="session-id",
        token_type="refresh",
    )
    request = _mock_request_with_refresh_cookie(refresh_jwt)
    response = Response()
    mock_user = Mock()
    mock_user.disabled = False
    mock_get_user.return_value = mock_user

    payload = refresh_token(request, response)

    assert payload["access_token"] is None
    assert payload["token_type"] == "bearer"
