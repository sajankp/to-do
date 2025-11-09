import logging
import sys
from datetime import timedelta
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.concurrency import asynccontextmanager
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from app.database.mongodb import mongodb_client
from app.models.base import PyObjectId
from app.models.user import CreateUser, Token
from app.routers.auth import (
    authenticate_user,
    create_token,
    get_user_by_username,
    get_user_info_from_token,
    hash_password,
)
from app.routers.auth import router as auth_router
from app.routers.todo import router as todo_router
from app.routers.user import router as user_router
from app.utils.constants import FAILED_TO_CREATE_USER, MISSING_TOKEN
from app.utils.health import app_check_health, check_app_readiness
from app.utils.validate_env import validate_env

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@asynccontextmanager
async def lifespan(application: FastAPI):
    settings = validate_env()
    if not await check_app_readiness():
        logging.error("Application failed to start.")
        sys.exit(1)
    application.mongodb_client = mongodb_client
    application.database = application.mongodb_client[settings.mongo_db]
    application.todo = application.database[settings.mongo_todo_collection]
    application.user = application.database[settings.mongo_user_collection]
    application.settings = settings
    yield
    application.mongodb_client.close()


app = FastAPI(lifespan=lifespan)

app.include_router(todo_router, prefix="/todo", tags=["todo"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(user_router, prefix="/user", tags=["user"])


@app.middleware("http")
async def add_user_info_to_request(request: Request, call_next):
    if request.url.path in (
        "/token",
        "/docs",
        "/openapi.json",
        "/",
        "/token/refresh",
        "/health",
    ):
        response = await call_next(request)
        return response
    try:
        token = request.headers.get("Authorization")
        if not token:
            return JSONResponse(
                content={"detail": MISSING_TOKEN},
                status_code=status.HTTP_401_UNAUTHORIZED,
                headers={"WWW-Authenticate": "Bearer"},
            )
        else:
            username, user_id = get_user_info_from_token(
                request.headers.get("Authorization")
            )
            request.state.user_id = PyObjectId(user_id)
            request.state.username = username
            response = await call_next(request)
            return response
    except HTTPException as e:
        return JSONResponse(
            content={"detail": str(e.detail)},
            status_code=e.status_code,
            headers={"WWW-Authenticate": "Bearer"},
        )


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}


@app.get("/health")
def check_health(token: str = Depends(oauth2_scheme)):
    return app_check_health(app)


@app.post("/token", response_model=Token)
def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], request: Request
):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(seconds=request.app.settings.access_token_expire_seconds)
    access_token = create_token(
        data={"sub": user.username, "sub_id": str(user.id)},
        expires_delta=access_token_expires,
    )
    refresh_token_expires = timedelta(seconds=request.app.settings.refresh_token_expire_seconds)
    refresh_token = create_token(
        data={"sub": user.username, "sub_id": str(user.id)},
        expires_delta=refresh_token_expires,
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@app.post("/token/refresh", response_model=Token)
def refresh_token(refresh_token: str, request: Request):
    username, user_id = get_user_info_from_token(refresh_token)
    if not username or not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    user = get_user_by_username(username)
    if not user or user.disabled:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    access_token_expires = timedelta(seconds=request.app.settings.access_token_expire_seconds)
    access_token = create_token(
        data={"sub": username, "sub_id": user_id},
        expires_delta=access_token_expires,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
    }


@app.post("/user", response_model=bool)
def create_user(username: str, email: str, password: str, request: Request):
    hashed_password = hash_password(password)
    user = CreateUser(username=username, email=email, hashed_password=hashed_password)
    # TODO: Pending testing and potential rework
    result = request.app.user.insert_one(user.model_dump())
    if result.acknowledged:
        return True
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=FAILED_TO_CREATE_USER,
        )
