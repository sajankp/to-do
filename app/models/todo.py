from datetime import datetime

from bson import ObjectId
from pydantic import BaseModel, Field, validator


class TodoBase(BaseModel):
    title: str = Field(...)
    description: str = Field(...)
    due_date: datetime = Field(...)
    priority: str = Field(...)
    """
    tags: List[str]
    assignee: str
    comments: List[str]
    attachments: List[str]
    Additional fields for future use
    estimated_time: int
    completed_at: datetime
    reminders: List[datetime]
    subtasks: List[str]
    project: str
    """

    @validator("due_date", pre=True, always=True)
    def parse_due_date(cls, value):
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(value)
        except (ValueError, TypeError):
            raise ValueError("Invalid datetime format")

    @validator("priority")
    def validate_priority(cls, value):
        # Validate priority to ensure it's one of the allowed values.
        if value not in ["low", "medium", "high"]:
            raise ValueError("Priority must be 'low', 'medium', or 'high'")
        return value

    class Config:
        orm_mode = True


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class TodoCreate(TodoBase):
    pass


class TodoUpdate(TodoBase):
    id: PyObjectId = Field(alias="_id")


class Todo(TodoBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(...)
    updated_at: datetime = Field(...)

    class Config:
        allow_population_by_field_name = True
        # to handle the id field as a string
        json_encoders = {ObjectId: str}
