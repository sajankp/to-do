from datetime import UTC, datetime
from enum import Enum

from pydantic import ConfigDict, Field, field_validator

from app.models.base import MyBaseModel, PyObjectId


class PriorityEnum(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class TodoBase(MyBaseModel):
    """Base model for todo items without validations - used for reading data."""

    title: str = Field(..., min_length=1, max_length=100, description="Todo title")
    description: str = Field(default="", max_length=500, description="Todo description")
    due_date: datetime | None = Field(default=None, description="Due date for the todo")
    priority: PriorityEnum = Field(default=PriorityEnum.medium, description="Todo priority")


class CreateTodo(TodoBase):
    """Model for creating new todos with validation."""

    @field_validator("due_date")
    @classmethod
    def validate_future_date(cls, v: datetime | None) -> datetime | None:
        """Ensure due_date is not in the past"""
        if v is not None and v < datetime.now(UTC):
            raise ValueError("Due date cannot be in the past")
        return v


class TodoUpdate(MyBaseModel):
    """Model for updating existing todos with validation."""

    title: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    due_date: datetime | None = Field(default=None)
    priority: PriorityEnum | None = Field(default=None)

    @field_validator("due_date")
    @classmethod
    def validate_future_date(cls, v: datetime | None) -> datetime | None:
        if v is not None:
            if v.tzinfo is None:
                v = v.replace(tzinfo=UTC)
            if v < datetime.now(UTC):
                raise ValueError("Due date cannot be in the past")
        return v

    model_config = ConfigDict(validate_assignment=True)


class TodoInDB(TodoBase, MyBaseModel):
    """
    Model representing a todo in the database.

    Inherits from:
    - TodoBase: title, description, due_date, priority
    - MyBaseModel: id, created_at, updated_at

    This model has ObjectId types (for database storage).
    """

    user_id: PyObjectId = Field(..., description="ID of the user who owns this todo")

    model_config = ConfigDict(
        populate_by_name=True,  # Allow both "id" and "_id"
        arbitrary_types_allowed=True,  # Allow ObjectId type
        validate_assignment=True,
        from_attributes=True,
    )


class TodoResponse(TodoBase):
    """
    Model for API responses.
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
