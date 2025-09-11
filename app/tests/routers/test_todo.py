import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock
from fastapi import Request
from bson import ObjectId

from app.models.todo import Todo, TodoBase, PriorityEnum
from app.models.base import PyObjectId
from app.routers.todo import create_todo, get_todo_list


class TestTodoRouter:
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
            due_date=datetime.now(timezone.utc),
            priority=PriorityEnum.medium
        )
        
        # Call the function
        result = create_todo(request, todo_data)
        
        # Assertions
        assert isinstance(result, Todo)
        assert result.title == "Test Todo"
        assert result.description == "Test Description"
        assert result.priority == PriorityEnum.medium
        assert result.user_id == request.state.user_id
        assert result.id == mock_result.inserted_id
        
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
        sample_todos = [
            {
                "_id": ObjectId("507f1f77bcf86cd799439012"),
                "title": "Todo 1",
                "description": "Description 1",
                "due_date": datetime.now(timezone.utc),
                "priority": "medium",
                "user_id": user_id,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "_id": ObjectId("507f1f77bcf86cd799439013"),
                "title": "Todo 2", 
                "description": "Description 2",
                "due_date": datetime.now(timezone.utc),
                "priority": "high",
                "user_id": user_id,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
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
        assert result == sample_todos
        
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
            due_date=datetime.now(timezone.utc),
            priority=PriorityEnum.medium
        )
        
        # Call the function and expect HTTPException
        with pytest.raises(Exception) as exc_info:
            create_todo(request, todo_data)
        
        # Verify it's an HTTPException with correct status code
        assert exc_info.value.status_code == 500
        assert "Failed to create todo" in str(exc_info.value.detail)