import os
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pymongo.collection import Collection

from app.database.mongodb import get_user_collection
from app.models.user import User
from app.utils.constants import INVALID_TOKEN

router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY")
PASSWORD_ALGORITHM = os.getenv("PASSWORD_ALGORITHM")


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


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=PASSWORD_ALGORITHM)
    return encoded_jwt


def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_jwt_token(token)
    if payload is None:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        raise credentials_exception
    return payload


def authenticate_user(username: str, password: str, user_model: Collection):
    if user := user_model.find_one({"username": username}):
        verify_password(password, user["hashed_password"])
        user = User(**user)
        return user
    else:
        return None


def get_current_active_user(token: str = Depends(oauth2_scheme)) -> User:
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

    except JWTError:
        raise credentials_exception
    user_collection = get_user_collection()
    user = user_collection.find_one({"username": username})
    return User(**user)


def get_user_info_from_token(authorization: str = Depends(oauth2_scheme)) -> (str, str):
    credentials_exception = HTTPException(
        status_code=401,
        detail=INVALID_TOKEN,
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[PASSWORD_ALGORITHM])
        username: str = payload.get("sub")
        user_id: str = payload.get("sub_id")
        if None in (username, user_id):
            raise credentials_exception
    except JWTError as E:
        raise credentials_exception
    return username, user_id
