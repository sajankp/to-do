from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.models.base import PyObjectId
from app.models.todo import PriorityEnum, Todo, TodoBase, TodoUpdate


def future_utc_datetime():
    return datetime.now(timezone.utc) + timedelta(days=1)

def past_utc_datetime():
    return datetime.now(timezone.utc) - timedelta(days=1)


def test_valid_todo_base():
    todo = TodoBase(
        title="Test Task",
        description="Description here",
        due_date=future_utc_datetime(),
        priority=PriorityEnum.high,
    )
    assert todo.title == "Test Task"
    assert todo.priority == PriorityEnum.high
    assert isinstance(todo.due_date, datetime)


def test_missing_title():
    with pytest.raises(ValidationError) as e:
        TodoBase(description="No title")
    assert "field required" in str(e.value)


def test_todo_base_title_length():
    with pytest.raises(ValidationError):
        TodoBase(title="", description="desc")
    with pytest.raises(ValidationError):
        TodoBase(title="x" * 101, description="desc")


def test_invalid_due_date_past():
    with pytest.raises(ValidationError) as e:
        TodoBase(title="Test", due_date=past_utc_datetime())
    assert "Due date cannot be in the past" in str(e.value)


def test_invalid_due_date_format():
    user_id = PyObjectId("507f1f77bcf86cd799439011")
    with pytest.raises(ValidationError) as e:
        TodoBase(title="Test", due_date="notadate", user_id=user_id)
    assert "Invalid isoformat string" in str(e.value)


def test_default_priority():
    todo = TodoBase(title="Test task")
    assert todo.priority == PriorityEnum.medium


def test_todo_update_partial():
    # Only updating priority
    update = TodoUpdate(priority=PriorityEnum.low)
    assert update.priority == PriorityEnum.low
    assert update.title is None


def test_todo_extends_todobase():
    user_id = PyObjectId("507f1f77bcf86cd799439011")
    t = Todo(title="X", description="D", user_id=user_id)
    assert isinstance(t, TodoBase)
    assert t.title == "X"
