from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request, status

from app.config import get_settings
from app.models.health import HealthResponse, ReadinessResponse

router = APIRouter(tags=["health"])
settings = get_settings()


@router.get("/health", response_model=HealthResponse)
def health_check():
    """Liveness probe to check if the application is running."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(UTC),
        version=settings.app_version,
    )


@router.get("/health/ready", response_model=ReadinessResponse)
def readiness_check(request: Request):
    """Readiness probe to check if the application dependencies are available."""
    try:
        # Check MongoDB connection
        # Using 'ping' command which is lightweight
        request.app.mongodb_client.admin.command("ping")
        db_status = "connected"
    except Exception as e:
        # If DB is down, we are not ready
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable",
        ) from e

    return ReadinessResponse(
        status="ready",
        timestamp=datetime.now(UTC),
        checks={
            "database": db_status,
            "dependencies": "ok",
        },
    )
