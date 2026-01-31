from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Schema for liveness probe response"""

    status: Literal["healthy"] = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Current server timestamp")
    version: str = Field(..., description="Service version")


class ReadinessResponse(BaseModel):
    """Schema for readiness probe response"""

    status: Literal["ready"] = Field(..., description="Service readiness status")
    timestamp: datetime = Field(..., description="Current server timestamp")
    checks: dict[str, str] = Field(..., description="Status of individual dependencies")
