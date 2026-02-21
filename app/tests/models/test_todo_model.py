from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.models.base import PyObjectId
from app.models.todo import CreateTodo, PriorityEnum, TodoInDB, TodoInput, TodoUpdate


def future_utc_datetime():
    return datetime.now(UTC) + timedelta(days=1)


def past_utc_datetime():
    return datetime.now(UTC) - timedelta(days=1)


def test_valid_todo_input():
    todo = TodoInput(
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
        TodoInput(description="No title")
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


def test_todo_input_validation():
    """Test that TodoInput applies some basic validation"""
    # Test minimum title length
    with pytest.raises(ValidationError):
        TodoInput(title="")

    # Test maximum title length
    todo = TodoInput(title="x" * 100)  # Max length is 100
    assert len(todo.title) == 100

    # Test date parsing
    todo = TodoInput(
        title="Test",
        description="desc",
        due_date=datetime.strptime("2024-01-01", "%Y-%m-%d").replace(tzinfo=UTC),
    )
    assert isinstance(todo.due_date, datetime)


def test_default_priority():
    todo = TodoInput(title="Test task")
    assert todo.priority == PriorityEnum.medium


def test_todo_update_partial():
    """Test partial updates with TodoUpdate"""
    # Only updating priority
    update = TodoUpdate(priority=PriorityEnum.low)
    assert update.priority == PriorityEnum.low
    assert update.title is None
    assert update.description is None


def test_todo_update_validation():
    """Test that TodoUpdate validates fields when provided"""
    # Test title length validation
    with pytest.raises(ValidationError):
        TodoUpdate(title="x" * 101)

    # Test due date validation
    with pytest.raises(ValidationError) as e:
        TodoUpdate(due_date=past_utc_datetime())
    assert "Due date cannot be in the past" in str(e.value)

    # Test that None values are allowed (for partial updates)
    update = TodoUpdate(
        title=None,
        description=None,
        due_date=None,
    )
    assert update.title is None
    assert update.description is None
    assert update.due_date is None


def test_todo_indb_has_required_fields():
    user_id = PyObjectId("507f1f77bcf86cd799439011")
    t = TodoInDB(title="X", description="D", user_id=user_id)
    assert t.title == "X"
    assert t.user_id == user_id
    # Verify system fields exist
    assert hasattr(t, "id")
    assert hasattr(t, "created_at")
    assert hasattr(t, "updated_at")


def test_create_todo_rejects_system_fields():
    """Verify CreateTodo does not accept id, created_at, updated_at."""
    # Create with extra fields that should be ignored
    todo = CreateTodo(
        title="Test",
        id="507f1f77bcf86cd799439011",
        _id="507f1f77bcf86cd799439011",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    # These fields should NOT be present on the model
    assert not hasattr(todo, "id")
    assert not hasattr(todo, "_id")
    assert not hasattr(todo, "created_at")
    assert not hasattr(todo, "updated_at")


def test_todo_update_rejects_system_fields():
    """Verify TodoUpdate does not accept id, created_at, updated_at."""
    update = TodoUpdate(
        title="Updated Title",
        id="507f1f77bcf86cd799439011",
        _id="507f1f77bcf86cd799439011",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    # These fields should NOT be present on the model
    assert not hasattr(update, "id")
    assert not hasattr(update, "_id")
    assert not hasattr(update, "created_at")
    assert not hasattr(update, "updated_at")


# ── Completed field tests (Spec-001) ──────────────────────────────


def test_todo_input_completed_default_false():
    """TodoInput should default completed to False."""
    todo = TodoInput(title="Test Task")
    assert todo.completed is False


def test_todo_input_completed_true():
    """TodoInput should accept completed=True."""
    todo = TodoInput(title="Done Task", completed=True)
    assert todo.completed is True


def test_todo_update_completed_optional():
    """TodoUpdate should allow completed as an optional field."""
    update = TodoUpdate(completed=True)
    assert update.completed is True
    # When not set, should remain None
    update_empty = TodoUpdate(title="Updated")
    assert update_empty.completed is None


def test_todo_indb_completed_default_false():
    """TodoInDB should default completed to False."""
    user_id = PyObjectId("507f1f77bcf86cd799439011")
    t = TodoInDB(title="X", description="D", user_id=user_id)
    assert t.completed is False


def test_create_todo_completed_default_false():
    """CreateTodo should default completed to False."""
    todo = CreateTodo(title="New Task")
    assert todo.completed is False
