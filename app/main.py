import logging
import os
import sys
from datetime import timedelta
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm

from app.database import get_mongo_client
from app.models.base import PyObjectId
from app.models.user import CreateUser, Token
from app.routers.auth import (
    authenticate_user,
    create_access_token,
    get_user_info_from_token,
    hash_password,
)
from app.routers.auth import router as auth_router
from app.routers.todo import router as todo_router
from app.routers.user import router as user_router
from app.utils.constants import FAILED_TO_CREATE_USER, MISSING_TOKEN
from app.utils.health import app_check_health, check_app_readiness

app = FastAPI()

app.include_router(todo_router, prefix="/todo", tags=["todo"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(user_router, prefix="/user", tags=["user"])

ACCESS_TOKEN_EXPIRE_SECONDS = os.getenv("ACCESS_TOKEN_EXPIRE_SECONDS")


@app.middleware("http")
async def add_user_info_to_request(request: Request, call_next):
    if request.url.path in ("/token", "/user", "/docs", "/openapi.json"):
        response = await call_next(request)
        return response
    try:
        token = request.headers.get("Authorization")
        if not token:
            response = JSONResponse(
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
    except HTTPException as e:
        response = JSONResponse(
            content={"detail": str(e.detail)},
            status_code=e.status_code,
            headers={"WWW-Authenticate": "Bearer"},
        )
    return response


@app.on_event("startup")
async def startup():
    # Wait for the application to be ready before continuing
    if not await check_app_readiness():
        logging.error("Application failed to start.")
        sys.exit(1)
    app.mongodb_client = get_mongo_client()
    app.database = app.mongodb_client[os.getenv("MONGO_DATABASE")]
    app.todo = app.database[os.getenv("MONGO_TODO_COLLECTION")]
    app.user = app.database[os.getenv("MONGO_USER_COLLECTION")]


@app.on_event("shutdown")
async def shutdown():
    if hasattr(app, "mongodb_client"):
        app.mongodb_client.close()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/health")
def check_health():
    return app_check_health(app)


@app.post("/token", response_model=Token)
def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], request: Request
):
    user = authenticate_user(form_data.username, form_data.password, request.app.user)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(seconds=int(ACCESS_TOKEN_EXPIRE_SECONDS))
    access_token = create_access_token(
        data={"sub": user.username, "sub_id": str(user.id)},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/user", response_model=bool)
def create_user(username: str, email: str, password: str, request: Request):
    hashed_password = hash_password(password)
    user = CreateUser(username=username, email=email, hashed_password=hashed_password)
    result = request.app.user.insert_one(user.dict())
    if result.acknowledged:
        return True
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=FAILED_TO_CREATE_USER,
        )
