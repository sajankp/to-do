from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, validator

from app.models.base import MyBaseModel, PyObjectId


class PriorityEnum(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class TodoBase(MyBaseModel):
    """Base model for todo items without validations - used for reading data."""

    title: str
    description: Optional[str] = ""
    due_date: Optional[str | datetime] = None  # Accept either string or datetime
    priority: PriorityEnum = PriorityEnum.medium

    class Config:
        orm_mode = True
        validate_assignment = True


class CreateTodo(TodoBase):
    """Model for creating new todos with validation."""

    title: str = Field(..., min_length=1, max_length=100, description="Todo title")
    description: str = Field("", max_length=500, description="Todo description")
    due_date: Optional[datetime] = Field(None, description="Due date for the todo")
    priority: PriorityEnum = Field(PriorityEnum.medium, description="Todo priority")

    @validator("due_date")
    def validate_future_date(cls, v):
        if v is not None and v < datetime.now(timezone.utc):
            raise ValueError("Due date cannot be in the past.")
        return v

    class Config:
        validate_assignment = True
        json_encoders = {datetime: lambda v: v.isoformat()}

    class Config:
        orm_mode = True


class TodoUpdate(MyBaseModel):
    """Model for updating existing todos with validation."""

    id: PyObjectId = Field(
        default_factory=PyObjectId, alias="_id"
    )  # Required for identifying the todo to update
    title: Optional[str] = Field(
        None, min_length=1, max_length=100, description="Updated todo title"
    )
    description: Optional[str] = Field(
        None, max_length=500, description="Updated todo description"
    )
    due_date: Optional[datetime] = Field(None, description="Updated due date")
    priority: Optional[PriorityEnum] = Field(None, description="Updated priority")

    @validator("due_date")
    def validate_future_date(cls, v):
        if v is not None and v < datetime.now(timezone.utc):
            raise ValueError("Due date cannot be in the past")
        return v

    class Config:
        allow_population_by_field_name = True
        validate_assignment = True


class Todo(TodoBase, MyBaseModel):
    user_id: PyObjectId = Field(..., description="ID of the user who owns this todo")
