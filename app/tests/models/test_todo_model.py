from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.models.base import PyObjectId
from app.models.todo import CreateTodo, PriorityEnum, TodoBase, TodoInDB, TodoUpdate


def future_utc_datetime():
    return datetime.now(UTC) + timedelta(days=1)


def past_utc_datetime():
    return datetime.now(UTC) - timedelta(days=1)


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
    assert "Field required" in str(e.value)


def test_todo_create_title_length():
    """Test title length validation for CreateTodo"""
    with pytest.raises(ValidationError):
        CreateTodo(title="", description="desc")
    with pytest.raises(ValidationError):
        CreateTodo(title="x" * 101, description="desc")


def test_create_todo_invalid_due_date_past():
    """Test due date validation for CreateTodo"""
    with pytest.raises(ValidationError) as e:
        CreateTodo(title="Test", due_date=past_utc_datetime())
    assert "Due date cannot be in the past" in str(e.value)


def test_create_todo_invalid_due_date_format():
    """Test date format validation for CreateTodo"""
    with pytest.raises(ValidationError) as e:
        CreateTodo(title="Test", due_date="notadate")
    assert "valid datetime" in str(e.value)


def test_todo_base_validation():
    """Test that TodoBase applies some basic validation"""
    # Test minimum title length
    with pytest.raises(ValidationError):
        TodoBase(title="")

    # Test maximum title length
    todo = TodoBase(title="x" * 100)  # Max length is 100
    assert len(todo.title) == 100

    # Test date parsing
    todo = TodoBase(
        title="Test",
        description="desc",
        due_date=datetime.strptime("2024-01-01", "%Y-%m-%d").replace(tzinfo=UTC),
    )
    assert isinstance(todo.due_date, datetime)


def test_default_priority():
    todo = TodoBase(title="Test task")
    assert todo.priority == PriorityEnum.medium


def test_todo_update_partial():
    """Test partial updates with TodoUpdate"""
    # Only updating priority
    update = TodoUpdate(id=PyObjectId("507f1f77bcf86cd799439011"), priority=PriorityEnum.low)
    assert update.priority == PriorityEnum.low
    assert update.title is None
    assert update.description is None


def test_todo_update_validation():
    """Test that TodoUpdate validates fields when provided"""
    # Test title length validation
    with pytest.raises(ValidationError):
        TodoUpdate(id=PyObjectId("507f1f77bcf86cd799439011"), title="x" * 101)

    # Test due date validation
    with pytest.raises(ValidationError) as e:
        TodoUpdate(id=PyObjectId("507f1f77bcf86cd799439011"), due_date=past_utc_datetime())
    assert "Due date cannot be in the past" in str(e.value)

    # Test that None values are allowed (for partial updates)
    update = TodoUpdate(
        id=PyObjectId("507f1f77bcf86cd799439011"),
        title=None,
        description=None,
        due_date=None,
    )
    assert update.title is None
    assert update.description is None
    assert update.due_date is None


def test_todo_extends_todobase():
    user_id = PyObjectId("507f1f77bcf86cd799439011")
    t = TodoInDB(title="X", description="D", user_id=user_id)
    assert isinstance(t, TodoBase)
    assert t.title == "X"
