from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import pytest
from bson import ObjectId
from fastapi import HTTPException, Request

from app.models.base import PyObjectId
from app.models.todo import PriorityEnum, TodoBase, TodoResponse
from app.routers.todo import create_todo, delete_todo, get_todo, get_todo_list
from app.utils.constants import (
    FAILED_CREATE_TODO,
    FAILED_DELETE_TODO,
    TODO_DELETED_SUCCESSFULLY,
    TODO_NOT_FOUND,
)


class TestTodoUserAssociation:
    """Test cases specifically for the todo-user association bug we fixed"""

    def test_create_todo_associates_with_correct_user(self):
        """Test that created todos are properly associated with the authenticated user"""
        # Mock request object with specific user
        request = Mock(spec=Request)
        user_id = PyObjectId("507f1f77bcf86cd799439011")
        request.state.user_id = user_id

        # Mock database collection
        mock_collection = Mock()
        mock_result = Mock()
        mock_result.acknowledged = True
        mock_result.inserted_id = ObjectId("507f1f77bcf86cd799439012")
        mock_collection.insert_one.return_value = mock_result
        request.app.todo = mock_collection

        # Create test todo data
        todo_data = TodoBase(
            title="User's Todo",
            description="This should belong to the user",
            due_date=datetime.now(UTC) + timedelta(seconds=60),
            priority=PriorityEnum.high,
        )

        # Call the function
        result = create_todo(request, todo_data)

        # Critical assertion: verify user_id is set correctly
        assert str(result.user_id) == str(user_id), "Todo must be associated with the correct user"

        # Verify the database call includes the user_id
        mock_collection.insert_one.assert_called_once()
        call_args = mock_collection.insert_one.call_args[0][0]
        assert call_args["user_id"] == user_id, "Database insert must include user_id"
        assert "user_id" in call_args, "user_id field must be present in database document"

    def test_get_todo_list_filters_by_user(self):
        """Test that todo listing only returns todos belonging to the authenticated user"""
        # Mock request object with specific user
        request = Mock(spec=Request)
        user_id = PyObjectId("507f1f77bcf86cd799439011")
        request.state.user_id = user_id

        # Mock database collection
        mock_collection = Mock()
        user_todos = [
            {
                "_id": ObjectId("507f1f77bcf86cd799439012"),
                "title": "User's Todo 1",
                "description": "Belongs to user",
                "due_date": datetime.now(UTC),
                "priority": "medium",
                "user_id": user_id,  # Same user
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            },
            {
                "_id": ObjectId("507f1f77bcf86cd799439013"),
                "title": "User's Todo 2",
                "description": "Also belongs to user",
                "due_date": datetime.now(UTC),
                "priority": "high",
                "user_id": user_id,  # Same user
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            },
        ]

        # Mock the find method to return user's todos
        mock_cursor = Mock()
        mock_cursor.limit.return_value = user_todos
        mock_collection.find.return_value = mock_cursor
        request.app.todo = mock_collection

        # Call the function
        result = get_todo_list(request)

        # Critical assertion: verify filtering by user_id
        mock_collection.find.assert_called_once_with({"user_id": user_id})
        assert len(result) == 2

        # Verify all returned todos belong to the user
        for todo in result:
            assert str(todo.user_id) == str(
                user_id
            ), "All todos must belong to the authenticated user"

    def test_get_todo_list_excludes_other_users_todos(self):
        """Test that todo listing doesn't return todos from other users"""
        # Mock request object with specific user
        request = Mock(spec=Request)
        user_id = PyObjectId("507f1f77bcf86cd799439011")
        other_user_id = PyObjectId("507f1f77bcf86cd799439999")
        request.state.user_id = user_id

        # Mock database collection - simulate database with mixed todos
        mock_collection = Mock()
        # Only user's todos should be returned (other user's todos filtered out by query)
        user_only_todos = [
            {
                "_id": ObjectId("507f1f77bcf86cd799439012"),
                "title": "User's Todo",
                "description": "Belongs to authenticated user",
                "due_date": datetime.now(UTC),
                "priority": "medium",
                "user_id": user_id,
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            }
        ]

        mock_cursor = Mock()
        mock_cursor.limit.return_value = user_only_todos
        mock_collection.find.return_value = mock_cursor
        request.app.todo = mock_collection

        # Call the function
        result = get_todo_list(request)

        # Critical assertion: verify query filters by user_id
        mock_collection.find.assert_called_once_with({"user_id": user_id})

        # Verify no other user's todos are returned
        for todo in result:
            assert str(todo.user_id) == str(user_id)
            assert str(todo.user_id) != str(
                other_user_id
            ), "Other user's todos must not be returned"

    def test_create_todo_without_user_id_fails(self):
        """Test that todo creation fails if user_id is not set in request state"""
        # Mock request object without user_id
        request = Mock(spec=Request)
        request.state = Mock()
        # Simulate missing user_id (this should not happen with proper middleware)
        request.state.user_id = None

        # Mock database collection
        mock_collection = Mock()
        request.app.todo = mock_collection

        # Create test todo data
        todo_data = TodoBase(
            title="Orphaned Todo",
            description="This should fail",
            due_date=datetime.now(UTC) + timedelta(seconds=60),
            priority=PriorityEnum.low,
        )

        # This should fail during validation
        with pytest.raises(ValueError):
            create_todo(request, todo_data)

    def test_todo_model_requires_user_id(self):
        """Test that Todo model requires user_id field"""
        current_time = datetime.now(UTC)
        user_id = PyObjectId("507f1f77bcf86cd799439011")

        # Test successful creation with user_id
        todo_with_user = TodoResponse(
            id=str(ObjectId()),
            title="Test Todo",
            description="Test Description",
            due_date=current_time + timedelta(seconds=60),
            priority=PriorityEnum.medium,
            user_id=str(user_id),
            created_at=current_time,
            updated_at=current_time,
        )
        assert str(todo_with_user.user_id) == str(user_id)

        # Test that user_id is required
        # Note: TodoResponse requires user_id, so this test validates the model contract
        with pytest.raises(ValueError):
            # This should fail because user_id is required in TodoResponse
            TodoResponse(
                id=str(ObjectId()),
                title="Test Todo",
                description="Test Description",
                due_date=current_time,
                priority=PriorityEnum.medium,
                # Missing user_id - should fail
                created_at=current_time,
                updated_at=current_time,
            )

    def test_create_and_list_integration(self):
        """Integration test: create todo and verify it appears in user's list"""
        # Mock request object with specific user
        request = Mock(spec=Request)
        user_id = PyObjectId("507f1f77bcf86cd799439011")
        request.state.user_id = user_id

        # Mock database collection for creation
        mock_collection = Mock()
        mock_result = Mock()
        mock_result.acknowledged = True
        todo_id = ObjectId("507f1f77bcf86cd799439012")
        mock_result.inserted_id = todo_id
        mock_collection.insert_one.return_value = mock_result
        request.app.todo = mock_collection

        # Create test todo data
        todo_data = TodoBase(
            title="Integration Test Todo",
            description="Should appear in user's list",
            due_date=datetime.now(UTC) + timedelta(seconds=60),
            priority=PriorityEnum.medium,
        )

        # Step 1: Create the todo
        created_todo = create_todo(request, todo_data)
        assert str(created_todo.user_id) == str(user_id)

        # Step 2: Mock the list query to return the created todo
        created_todo_dict = {
            "_id": todo_id,
            "title": "Integration Test Todo",
            "description": "Should appear in user's list",
            "due_date": created_todo.due_date,
            "priority": "medium",
            "user_id": user_id,
            "created_at": created_todo.created_at,
            "updated_at": created_todo.updated_at,
        }

        mock_cursor = Mock()
        mock_cursor.limit.return_value = [created_todo_dict]
        mock_collection.find.return_value = mock_cursor

        # Step 3: List todos and verify the created todo appears
        todos = get_todo_list(request)

        assert len(todos) == 1
        assert str(todos[0].id) == str(todo_id)
        assert str(todos[0].user_id) == str(user_id)
        assert todos[0].title == "Integration Test Todo"

        # Verify the list query filtered by user_id
        mock_collection.find.assert_called_with({"user_id": user_id})


class TestTodoRouter:
    """Original test cases plus additional edge cases"""

    def test_create_todo_success(self):
        # Mock request object
        request = Mock(spec=Request)
        request.state.user_id = PyObjectId("507f1f77bcf86cd799439011")

        # Mock database collection
        mock_collection = Mock()
        mock_result = Mock()
        mock_result.acknowledged = True
        mock_result.inserted_id = ObjectId("507f1f77bcf86cd799439012")
        mock_collection.insert_one.return_value = mock_result
        request.app.todo = mock_collection

        # Create test todo data
        todo_data = TodoBase(
            title="Test Todo",
            description="Test Description",
            due_date=datetime.now(UTC) + timedelta(seconds=60),
            priority=PriorityEnum.medium,
        )

        # Call the function
        result = create_todo(request, todo_data)

        # Assertions
        assert isinstance(result, TodoResponse)
        assert result.title == "Test Todo"
        assert result.description == "Test Description"
        assert result.priority == PriorityEnum.medium
        assert str(result.user_id) == str(request.state.user_id)
        assert str(result.id) == str(mock_result.inserted_id)

        # Verify database call
        mock_collection.insert_one.assert_called_once()
        call_args = mock_collection.insert_one.call_args[0][0]
        assert call_args["title"] == "Test Todo"
        assert call_args["user_id"] == request.state.user_id

    def test_get_todo_list_success(self):
        # Mock request object
        request = Mock(spec=Request)
        user_id = PyObjectId("507f1f77bcf86cd799439011")
        request.state.user_id = user_id

        # Mock database collection with sample todos
        mock_collection = Mock()
        now = datetime.now(UTC)
        sample_todos = [
            {
                "_id": ObjectId("507f1f77bcf86cd799439012"),
                "title": "Todo 1",
                "description": "Description 1",
                "due_date": now + timedelta(seconds=60),
                "priority": "medium",
                "user_id": user_id,
                "created_at": now,
                "updated_at": now,
            },
            {
                "_id": ObjectId("507f1f77bcf86cd799439013"),
                "title": "Todo 2",
                "description": "Description 2",
                "due_date": now + timedelta(seconds=60),
                "priority": "high",
                "user_id": user_id,
                "created_at": now,
                "updated_at": now,
            },
        ]

        # Mock the find method to return our sample todos
        mock_cursor = Mock()
        mock_cursor.limit.return_value = sample_todos
        mock_collection.find.return_value = mock_cursor
        request.app.todo = mock_collection

        # Call the function
        result = get_todo_list(request)

        # Assertions
        assert len(result) == 2
        # Verify individual fields since model conversion changes the format
        for actual, expected in zip(result, sample_todos, strict=True):
            assert str(actual.id) == str(expected["_id"])
            assert actual.title == expected["title"]
            assert actual.description == expected["description"]
            assert str(actual.user_id) == str(expected["user_id"])
            assert actual.priority.value == expected["priority"]

        # Verify database call with correct user filter
        mock_collection.find.assert_called_once_with({"user_id": user_id})
        mock_cursor.limit.assert_called_once_with(100)

    def test_create_todo_database_failure(self):
        # Mock request object
        request = Mock(spec=Request)
        request.state.user_id = PyObjectId("507f1f77bcf86cd799439011")

        # Mock database collection with failure
        mock_collection = Mock()
        mock_result = Mock()
        mock_result.acknowledged = False
        mock_collection.insert_one.return_value = mock_result
        request.app.todo = mock_collection

        # Create test todo data
        todo_data = TodoBase(
            title="Test Todo",
            description="Test Description",
            due_date=datetime.now(UTC) + timedelta(seconds=60),
            priority=PriorityEnum.medium,
        )

        # Call the function and expect HTTPException
        with pytest.raises(HTTPException) as exc_info:
            create_todo(request, todo_data)

        # Verify it's an HTTPException with correct status code
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == FAILED_CREATE_TODO

    def test_get_todo_by_id_success(self):
        """Test retrieving a specific todo by ID"""
        request = Mock(spec=Request)
        todo_id = PyObjectId("507f1f77bcf86cd799439012")
        user_id = PyObjectId("507f1f77bcf86cd799439011")
        request.state.user_id = user_id

        # Mock database collection
        mock_collection = Mock()
        now = datetime.now(UTC)
        sample_todo = {
            "_id": todo_id,
            "title": "Test Todo",
            "description": "Test Description",
            "due_date": now,
            "priority": "medium",
            "user_id": user_id,
            "created_at": now,
            "updated_at": now,
        }
        mock_collection.find_one.return_value = sample_todo
        request.app.todo = mock_collection

        # Call the function
        result = get_todo(todo_id, request)

        # Assertions
        assert str(result.id) == str(sample_todo["_id"])
        assert result.title == sample_todo["title"]
        assert result.description == sample_todo["description"]
        assert str(result.user_id) == str(sample_todo["user_id"])
        assert result.priority.value == sample_todo["priority"]
        mock_collection.find_one.assert_called_once_with({"_id": todo_id, "user_id": user_id})

    def test_get_todo_by_id_not_found(self):
        """Test retrieving a non-existent todo"""
        request = Mock(spec=Request)
        todo_id = PyObjectId("507f1f77bcf86cd799439012")

        # Mock database collection returning None
        mock_collection = Mock()
        mock_collection.find_one.return_value = None
        request.app.todo = mock_collection

        # Call the function and expect HTTPException
        with pytest.raises(HTTPException) as exc_info:
            get_todo(todo_id, request)

        # Verify it's a 404 error
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == TODO_NOT_FOUND

    def test_delete_todo_success(self):
        """Test successful todo deletion"""
        request = Mock(spec=Request)
        todo_id = PyObjectId("507f1f77bcf86cd799439012")

        # Mock database collection
        mock_collection = Mock()
        # Mock existing todo
        mock_collection.find_one.return_value = {"_id": todo_id, "title": "Test"}
        # Mock successful deletion
        mock_delete_result = Mock()
        mock_delete_result.deleted_count = 1
        mock_collection.delete_one.return_value = mock_delete_result
        request.app.todo = mock_collection

        # Call the function
        result = delete_todo(todo_id, request)

        # Assertions
        assert result["message"] == TODO_DELETED_SUCCESSFULLY
        mock_collection.find_one.assert_called_once_with({"_id": todo_id})
        mock_collection.delete_one.assert_called_once_with({"_id": todo_id})

    def test_delete_todo_not_found(self):
        """Test deleting a non-existent todo"""
        request = Mock(spec=Request)
        todo_id = PyObjectId("507f1f77bcf86cd799439012")

        # Mock database collection returning None for find_one
        mock_collection = Mock()
        mock_collection.find_one.return_value = None
        request.app.todo = mock_collection

        # Call the function and expect HTTPException
        with pytest.raises(HTTPException) as exc_info:
            delete_todo(todo_id, request)

        # Verify it's a 404 error
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == TODO_NOT_FOUND

    def test_delete_todo_database_failure(self):
        """Test todo deletion database failure"""
        request = Mock(spec=Request)
        todo_id = PyObjectId("507f1f77bcf86cd799439012")

        # Mock database collection
        mock_collection = Mock()
        # Mock existing todo
        mock_collection.find_one.return_value = {"_id": todo_id, "title": "Test"}
        # Mock failed deletion
        mock_delete_result = Mock()
        mock_delete_result.deleted_count = 0
        mock_collection.delete_one.return_value = mock_delete_result
        request.app.todo = mock_collection

        # Call the function and expect HTTPException
        with pytest.raises(HTTPException) as exc_info:
            delete_todo(todo_id, request)

        # Verify it's a 500 error
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == FAILED_DELETE_TODO
