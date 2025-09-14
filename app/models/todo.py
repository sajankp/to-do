from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, validator

from app.models.base import MyBaseModel, PyObjectId


class PriorityEnum(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"

class TodoBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field("", max_length=500)
    due_date: Optional[datetime] = Field(None)
    priority: PriorityEnum = Field(PriorityEnum.medium)

    @validator("due_date", pre=True, always=True)
    def parse_due_date(cls, value):
        if value is None:
            return value
        try:
            if isinstance(value, datetime):
                dt = value
            else:
                dt = datetime.fromisoformat(value)
            if dt < datetime.now(timezone.utc):
                raise ValueError("Due date cannot be in the past.")
            return dt
        except TypeError:
            raise ValueError("Invalid datetime format")

    class Config:
        orm_mode = True


class TodoUpdate(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    due_date: Optional[datetime]
    priority: Optional[PriorityEnum]

    @validator("due_date", pre=True, always=True)
    def parse_due_date(cls, value):
        if value is None:
            return value
        if isinstance(value, datetime):
            dt = value
        else:
            try:
                dt = datetime.fromisoformat(value)
            except (ValueError, TypeError):
                raise ValueError("Invalid datetime format")
        if dt < datetime.now(timezone.utc):
            raise ValueError("Due date cannot be in the past.")
        return dt

class Todo(TodoBase, MyBaseModel):
    user_id: PyObjectId = Field(..., description="ID of the user who owns this todo")
