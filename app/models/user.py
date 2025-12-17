from pydantic import BaseModel, EmailStr, Field

from app.models.base import MyBaseModel


class UserInput(BaseModel):
    """Base input model for user creation. NO system fields (id, created_at, updated_at)."""

    username: str = Field(..., description="Username for authentication")
    email: EmailStr = Field(..., description="User's email address")


class CreateUser(UserInput):
    """Model for user creation with password field."""

    hashed_password: str = Field(..., description="Hashed password for security")


class UserInDB(MyBaseModel):
    """Database model for user with system fields."""

    username: str = Field(..., description="Username for authentication")
    email: str = Field(..., description="User's email address")
    hashed_password: str = Field(..., description="Hashed password for security")
    is_verified: bool = Field(default=False, description="Email verification status")
    disabled: bool = Field(default=False, description="Account status")


class UserResponse(MyBaseModel):
    """Response model for user data - excludes sensitive fields like password."""

    username: str = Field(..., description="Username for authentication")
    email: str = Field(..., description="User's email address")
    is_verified: bool = Field(default=False, description="Email verification status")
    disabled: bool = Field(default=False, description="Account status")


class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str
