from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.base import MyBaseModel, PyObjectId


class PriorityEnum(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


def validate_future_due_date(v: datetime | None) -> datetime | None:
    """Validate that due_date is not in the past. Adds UTC timezone if missing."""
    if v is not None:
        if v.tzinfo is None:
            v = v.replace(tzinfo=UTC)
        if v < datetime.now(UTC):
            raise ValueError("Due date cannot be in the past")
    return v


class TodoInput(BaseModel):
    """Base input model for creating/updating todos. NO system fields (id, created_at, updated_at)."""

    title: str = Field(..., min_length=1, max_length=100, description="Todo title")
    description: str = Field(default="", max_length=500, description="Todo description")
    due_date: datetime | None = Field(default=None, description="Due date for the todo")
    priority: PriorityEnum = Field(default=PriorityEnum.medium, description="Todo priority")


class CreateTodo(TodoInput):
    """Model for creating new todos with validation."""

    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, v: datetime | None) -> datetime | None:
        """Ensure due_date is not in the past"""
        return validate_future_due_date(v)


class TodoUpdate(BaseModel):
    """Model for updating existing todos with validation. All fields optional for partial updates."""

    title: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    due_date: datetime | None = Field(default=None)
    priority: PriorityEnum | None = Field(default=None)

    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, v: datetime | None) -> datetime | None:
        return validate_future_due_date(v)

    model_config = ConfigDict(validate_assignment=True)


class TodoInDB(MyBaseModel):
    """
    Model representing a todo in the database.

    Inherits from MyBaseModel: id, created_at, updated_at
    Adds todo-specific fields: title, description, due_date, priority, user_id
    """

    title: str = Field(..., min_length=1, max_length=100, description="Todo title")
    description: str = Field(default="", max_length=500, description="Todo description")
    due_date: datetime | None = Field(default=None, description="Due date for the todo")
    priority: PriorityEnum = Field(default=PriorityEnum.medium, description="Todo priority")
    user_id: PyObjectId = Field(..., description="ID of the user who owns this todo")

    model_config = ConfigDict(
        populate_by_name=True,  # Allow both "id" and "_id"
        arbitrary_types_allowed=True,  # Allow ObjectId type
        validate_assignment=True,
        from_attributes=True,
    )


class TodoResponse(TodoInput):
    """
    Model for API responses. Includes system fields as read-only.
    """

    id: str = Field(..., description="Todo ID")
    user_id: str = Field(..., description="User ID")
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_db(cls, todo_db: TodoInDB) -> "TodoResponse":
        """
        Convert from database model to API response model.
        This is where ObjectId → string conversion happens!
        """
        return cls(
            id=str(todo_db.id),
            user_id=str(todo_db.user_id),
            title=todo_db.title,
            description=todo_db.description,
            due_date=todo_db.due_date,
            priority=todo_db.priority,
            created_at=todo_db.created_at,
            updated_at=todo_db.updated_at,
        )

    model_config = ConfigDict(
        from_attributes=True,
    )
