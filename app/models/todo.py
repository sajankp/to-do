from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, validator

from app.models.base import MyBaseModel, PyObjectId


class PriorityEnum(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class TodoBase(BaseModel):
    title: str
    description: str
    due_date: datetime
    priority: PriorityEnum

    @validator("due_date", pre=True, always=True)
    def parse_due_date(cls, value):
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(value)
        except (ValueError, TypeError):
            raise ValueError("Invalid datetime format")

    class Config:
        orm_mode = True


class TodoUpdate(TodoBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")


class Todo(TodoBase, MyBaseModel):
    pass
