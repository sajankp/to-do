from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings
from app.models.user import UserInDB
from app.utils.constants import INVALID_TOKEN
from app.utils.user import get_user_by_username

router = APIRouter()
settings = get_settings()

SECRET_KEY = settings.secret_key
PASSWORD_ALGORITHM = settings.password_algorithm

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_jwt_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=PASSWORD_ALGORITHM)


def decode_jwt_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[PASSWORD_ALGORITHM])
        return payload
    except JWTError:
        return None


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=PASSWORD_ALGORITHM)
    return encoded_jwt


def authenticate_user(username: str, password: str):
    user = get_user_by_username(username)
    if user and verify_password(password, user.hashed_password):
        return user
    else:
        return None


def get_current_active_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    credentials_exception = HTTPException(
        status_code=401,
        detail=INVALID_TOKEN,
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[PASSWORD_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError as e:
        raise credentials_exception from e
    user = get_user_by_username(username)
    if not user:
        raise credentials_exception
    return user


def get_user_info_from_token(authorization: str = Depends(oauth2_scheme)) -> (str, str):
    credentials_exception = HTTPException(
        status_code=401,
        detail=INVALID_TOKEN,
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = authorization.split(" ")[1] if authorization.startswith("Bearer") else authorization
        payload = jwt.decode(token, SECRET_KEY, algorithms=[PASSWORD_ALGORITHM])
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
