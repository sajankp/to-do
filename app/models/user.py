from pydantic import BaseModel, Field

from app.database.mongodb import get_user_collection
from app.models.base import MyBaseModel


class User(MyBaseModel):
    username: str = Field(...)
    email: str = Field(...)
    is_verified: bool = Field(default=False)
    disabled: bool = Field(default=False)


class CreateUser(User):
    hashed_password: str = Field(...)


class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str


def get_user_by_username(username: str) -> User:
    user_collection = get_user_collection()
    return user_collection.find_one({"username": username})
