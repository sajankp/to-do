import logging
import secrets
import sys
import uuid
from datetime import timedelta
from typing import Annotated

import pymongo.errors
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import get_settings
from app.database.mongodb import mongodb_client

# specific imports for logging
from app.middleware.logging import StructlogMiddleware
from app.middleware.security import SecurityHeadersMiddleware
from app.models.base import PyObjectId
from app.models.user import CreateUser, Token, UserRegistration
from app.routers.ai_stream import router as ai_stream_router
from app.routers.auth import (
    authenticate_user,
    create_token,
    get_user_by_username,
    get_user_info_from_token,
    hash_password,
)
from app.routers.auth import router as auth_router
from app.routers.health import router as health_router
from app.routers.todo import router as todo_router
from app.routers.user import router as user_router
from app.utils.constants import FAILED_TO_CREATE_USER, MISSING_TOKEN
from app.utils.health import check_app_readiness
from app.utils.jwt import decode_jwt_token
from app.utils.logging import setup_logging
from app.utils.metrics import LOGINS_TOTAL, REGISTRATIONS_TOTAL
from app.utils.rate_limiter import limiter
from app.utils.telemetry import setup_telemetry
from app.utils.validate_env import validate_env

# Initialize logging before creating the app
setup_logging()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
settings = get_settings()


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


def verify_metrics_token(request: Request):
    """Dependency to protect the /metrics endpoint."""
    if settings.metrics_bearer_token:
        # If token is configured, ENFORCE it strictly
        auth_header = request.headers.get("Authorization")
        expected_auth = f"Bearer {settings.metrics_bearer_token}"
        # Use constant-time comparison to prevent timing attacks
        if not (auth_header and secrets.compare_digest(auth_header, expected_auth)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden",
            )
    elif settings.metrics_dev_mode:
        # If no token but Dev Mode is enabled, allow public access
        # Ensure we log this potential risk in non-testing environments
        if settings.environment.lower() != "testing":
            logging.warning(
                "Metrics endpoint is publicly accessible due to METRICS_DEV_MODE=True. "
                "This is a security risk in a production environment."
            )
        pass
    else:
        # Default: DENY if no token and not in Dev Mode (Secure by Default)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Configure METRICS_BEARER_TOKEN or METRICS_DEV_MODE",
        )


setup_telemetry(app, settings)

# Setup Prometheus Metrics
Instrumentator().instrument(app).expose(app, dependencies=[Depends(verify_metrics_token)])

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
# Logging middleware should be one of the first to capture everything
app.add_middleware(StructlogMiddleware)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# Configure CORS (Must be last to ensure headers on all responses, including 429s)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.get_cors_methods_list(),
    allow_headers=settings.get_cors_headers_list(),
)

app.include_router(ai_stream_router, prefix="/api/ai", tags=["ai-stream"])
app.include_router(health_router, tags=["health"])
app.include_router(todo_router, prefix="/todo", tags=["todo"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(user_router, prefix="/user", tags=["user"])


@app.middleware("http")
async def add_user_info_to_request(request: Request, call_next):
    # Allow OPTIONS requests (CORS preflight) to pass through without authentication
    if request.method == "OPTIONS":
        response = await call_next(request)
        return response

    if request.url.path in (
        "/token",
        "/docs",
        "/openapi.json",
        "/",
        "/token/refresh",
        "/health",
        "/health/ready",
        "/user",
        "/api/ai/voice/stream",  # WebSocket authenticates via first message
        "/metrics",
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
            username, user_id = get_user_info_from_token(request.headers.get("Authorization"))
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


@app.post("/token", response_model=Token)
@limiter.limit(settings.rate_limit_auth)
def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], request: Request
):
    # Authenticate user
    user, new_hash = authenticate_user(form_data.username, form_data.password)
    if not user:
        LOGINS_TOTAL.labels(status="failed").inc()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    LOGINS_TOTAL.labels(status="success").inc()

    # Transparent migration: upgrade old bcrypt hashes to Argon2id
    if new_hash:
        try:
            request.app.user.update_one(
                {"username": user.username}, {"$set": {"hashed_password": new_hash}}
            )
        except pymongo.errors.PyMongoError as e:
            # Log warning but don't fail login
            logging.warning(f"Failed to upgrade password hash for {user.username}: {e}")

    # Generate a new Session ID (sid) for this login session
    sid = str(uuid.uuid4())

    access_token_expires = timedelta(seconds=settings.access_token_expire_seconds)
    access_token = create_token(
        data={"sub": user.username, "sub_id": str(user.id)},
        expires_delta=access_token_expires,
        sid=sid,
    )
    refresh_token_expires = timedelta(seconds=settings.refresh_token_expire_seconds)
    refresh_token = create_token(
        data={"sub": user.username, "sub_id": str(user.id)},
        expires_delta=refresh_token_expires,
        sid=sid,
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@app.post("/token/refresh", response_model=Token)
@limiter.limit(settings.rate_limit_auth)
def refresh_token(refresh_token: str, request: Request):
    # Decode the refresh token to extract user info and session ID
    payload = decode_jwt_token(refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    username = payload.get("sub")
    user_id = payload.get("sub_id")
    sid = payload.get("sid")  # Extract session ID from refresh token

    if not username or not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    user = get_user_by_username(username)
    if not user or user.disabled:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # Create new access token with the same session ID
    access_token_expires = timedelta(seconds=settings.access_token_expire_seconds)
    access_token = create_token(
        data={"sub": username, "sub_id": user_id},
        expires_delta=access_token_expires,
        sid=sid,  # Propagate session ID to maintain session tracking
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
    }


@app.post("/user", response_model=bool)
@limiter.limit(settings.rate_limit_auth)
def create_user(user_in: UserRegistration, request: Request):
    hashed_password = hash_password(user_in.password)
    user = CreateUser(
        username=user_in.username, email=user_in.email, hashed_password=hashed_password
    )
    result = request.app.user.insert_one(user.model_dump())
    if result.acknowledged:
        REGISTRATIONS_TOTAL.inc()
        return True
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=FAILED_TO_CREATE_USER,
        )
