import uuid
from pydantic import BaseModel, Field
from datetime import datetime


class TodoBase(BaseModel):
    title: str = Field(...)
    description: str = Field(...)
    due_date: datetime = Field(...)
    priority: str = Field(...)
    # tags: List[str]
    # assignee: str
    # comments: List[str]
    # attachments: List[str]
    # Additional fields for future use
    # estimated_time: int
    # completed_at: datetime
    # reminders: List[datetime]
    # subtasks: List[str]
    # project: str


class TodoCreate(TodoBase):
    pass


class TodoUpdate(TodoBase):
    status: str = Field(...)


class Todo(TodoBase):
    id: str = Field(default_factory=uuid.uuid4, alias="_id")
    created_at: datetime = Field(...)
    updated_at: datetime = Field(...)
