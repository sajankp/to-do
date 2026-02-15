from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from fastapi import APIRouter, HTTPException, Request
from jose import JWTError, jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from pwdlib.hashers.bcrypt import BcryptHasher

if TYPE_CHECKING:
    pass

from app.config import get_settings
from app.models.user import UserInDB
from app.utils.constants import INVALID_TOKEN
from app.utils.user import get_user_by_username

router = APIRouter()
settings = get_settings()

SECRET_KEY = settings.secret_key
PASSWORD_ALGORITHM = settings.password_algorithm

# oauth2_scheme removed in favor of strict cookie middleware
# Argon2id primary (first in list), bcrypt for legacy verification
pwd_hash = PasswordHash([Argon2Hasher(), BcryptHasher()])


def create_jwt_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=PASSWORD_ALGORITHM)


def hash_password(password: str):
    """Hash a password using Argon2id."""
    return pwd_hash.hash(password)


def verify_password(plain_password, hashed_password):
    """Verify password and return (is_valid, new_hash) for transparent migration.

    Returns:
        Tuple[bool, Optional[str]]: (is_valid, new_hash) where new_hash is set
        if the password used an old algorithm and needs upgrading.
    """
    return pwd_hash.verify_and_update(plain_password, hashed_password)


def create_token(
    data: dict,
    expires_delta: timedelta | None = None,
    sid: str | None = None,
    token_type: str | None = None,
):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=15)

    # Add Session ID (sid) to the token claims
    if sid:
        to_encode.update({"sid": sid})
    if token_type:
        to_encode.update({"token_type": token_type})

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=PASSWORD_ALGORITHM)
    return encoded_jwt


def authenticate_user(username: str, password: str, client):
    """Authenticate a user and return the user object and optional new hash.

    Returns:
        Tuple[Optional[UserInDB], Optional[str]]: (user, new_hash) where new_hash
        is set if password migration is needed, or (None, None) if auth fails.
    """
    user = get_user_by_username(username, client)
    if not user:
        return None, None

    is_valid, new_hash = verify_password(password, user.hashed_password)
    if not is_valid:
        return None, None

    return user, new_hash


def get_authenticated_user(request: Request) -> UserInDB:
    """
    Dependency that retrieves the authenticated user from the request state.
    This assumes that the `add_user_info_to_request` middleware has already
    validated the token and populated `request.state`.
    """
    if not hasattr(request.state, "user_id") or not request.state.user_id:
        # Should be caught by middleware, but doubly safe
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # We could return just the ID, or fetch the full user if needed.
    # To match previous behavior and ensure user exists in DB at this moment:
    client = request.app.mongodb_client
    user = get_user_by_username(request.state.username, client)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_user_info_from_token(token: str, expected_type: str = "access") -> (str, str):
    credentials_exception = HTTPException(
        status_code=401,
        detail=INVALID_TOKEN,
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # token = authorization.split(" ")[1] if authorization.startswith("Bearer") else authorization
        payload = jwt.decode(token, SECRET_KEY, algorithms=[PASSWORD_ALGORITHM])
        token_type: str | None = payload.get("token_type")
        if token_type != expected_type:
            raise credentials_exception
        username: str = payload.get("sub")
        user_id: str = payload.get("sub_id")
        if None in (username, user_id):
            raise credentials_exception
    except JWTError as e:
        if isinstance(e, jwt.ExpiredSignatureError):
            credentials_exception.detail = "Token has expired"
        else:
            credentials_exception.detail = f"JWTError: {str(e)}"
        raise credentials_exception from e
    return username, user_id
