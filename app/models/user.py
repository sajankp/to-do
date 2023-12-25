from pydantic import BaseModel, Field

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
