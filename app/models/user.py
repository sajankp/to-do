from pydantic import BaseModel, Field

from app.database.mongodb import get_user_collection
from app.models.base import MyBaseModel


class UserBase(MyBaseModel):
    """Base user model with common fields."""

    username: str = Field(..., description="Username for authentication")
    email: str = Field(..., description="User's email address")


class User(UserBase):
    """Full user model with additional status fields."""

    is_verified: bool = Field(default=False, description="Email verification status")
    disabled: bool = Field(default=False, description="Account status")


class CreateUser(UserBase):
    """Model for user creation with password field."""

    hashed_password: str = Field(..., description="Hashed password for security")


class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str


def get_user_by_username(username: str) -> User:
    user_collection = get_user_collection()
    return user_collection.find_one({"username": username})
