"""
Integration tests for todo-user association functionality.
These tests verify the complete flow from middleware to database operations.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, Mock, patch

import pytest
from bson import ObjectId
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.main import add_user_info_to_request
from app.models.base import PyObjectId
from app.models.todo import PriorityEnum


class TestTodoUserIntegration:
    """Integration tests for the todo-user association bug fix"""

    @pytest.fixture
    def mock_app(self):
        """Create a mock FastAPI app with necessary attributes"""
        app = Mock(spec=FastAPI)
        app.todo = Mock()
        app.user = Mock()
        return app

    @pytest.fixture
    def mock_request(self, mock_app):
        """Create a mock request with app attached"""
        request = Mock(spec=Request)
        request.app = mock_app
        request.url.path = "/todo/"
        request.headers = {"Authorization": "Bearer valid_token"}
        request.state = Mock()
        return request

    @patch('app.main.get_user_info_from_token')
    @pytest.mark.asyncio
    async def test_middleware_sets_user_id_correctly(self, mock_get_user_info, mock_request):
        """Test that middleware correctly sets user_id in request state"""
        # Mock the token validation
        test_username = "testuser"
        test_user_id = "507f1f77bcf86cd799439011"
        mock_get_user_info.return_value = (test_username, test_user_id)

        # Mock the next call
        async def mock_call_next(request):
            # Verify that user_id was set in request state
            assert hasattr(request.state, 'user_id')
            assert hasattr(request.state, 'username')
            assert request.state.username == test_username
            assert isinstance(request.state.user_id, PyObjectId)
            assert str(request.state.user_id) == test_user_id
            return Mock(status_code=200)

        # Call the middleware
        response = await add_user_info_to_request(mock_request, mock_call_next)

        # Verify the middleware processed correctly
        assert response.status_code == 200
        mock_get_user_info.assert_called_once_with("Bearer valid_token")

    @patch('app.main.get_user_info_from_token')
    @pytest.mark.asyncio
    async def test_middleware_handles_missing_token(self, mock_get_user_info):
        """Test that middleware returns 401 when token is missing"""
        # Create request without Authorization header
        request = Mock(spec=Request)
        request.url.path = "/todo/"
        request.headers = {}

        async def mock_call_next(request):
            return Mock(status_code=200)

        # Call the middleware
        response = await add_user_info_to_request(request, mock_call_next)

        # Verify 401 response
        assert response.status_code == 401
        assert "Missing Token" in str(response.body)
        mock_get_user_info.assert_not_called()

    @patch('app.main.get_user_info_from_token')
    @pytest.mark.asyncio
    async def test_middleware_handles_invalid_token(self, mock_get_user_info, mock_request):
        """Test that middleware returns 401 when token is invalid"""
        from fastapi import HTTPException

        # Mock token validation to raise HTTPException
        mock_get_user_info.side_effect = HTTPException(
            status_code=401, 
            detail="Invalid token"
        )

        async def mock_call_next(request):
            return Mock(status_code=200)

        # Call the middleware
        response = await add_user_info_to_request(mock_request, mock_call_next)

        # Verify 401 response
        assert response.status_code == 401
        assert "Invalid token" in str(response.body)

    def test_todo_creation_with_user_association(self, mock_request):
        """Test complete todo creation flow with user association"""
        from app.models.todo import TodoBase
        from app.routers.todo import create_todo

        # Set up request state (simulating middleware)
        user_id = PyObjectId("507f1f77bcf86cd799439011")
        mock_request.state.user_id = user_id
        mock_request.state.username = "testuser"

        # Mock database operations
        mock_result = Mock()
        mock_result.acknowledged = True
        mock_result.inserted_id = ObjectId("507f1f77bcf86cd799439012")
        mock_request.app.todo.insert_one.return_value = mock_result

        # Create todo data
        todo_data = TodoBase(
            title="Integration Test Todo",
            description="Testing user association",
            due_date=datetime.now(timezone.utc) + timedelta(seconds=60),
            priority=PriorityEnum.high,
        )

        # Create the todo
        result = create_todo(mock_request, todo_data)

        # Verify user association
        assert result.user_id == user_id
        assert result.title == "Integration Test Todo"

        # Verify database call included user_id
        mock_request.app.todo.insert_one.assert_called_once()
        call_args = mock_request.app.todo.insert_one.call_args[0][0]
        assert call_args["user_id"] == user_id

    def test_todo_listing_with_user_filtering(self, mock_request):
        """Test complete todo listing flow with user filtering"""
        from app.routers.todo import get_todo_list

        # Set up request state (simulating middleware)
        user_id = PyObjectId("507f1f77bcf86cd799439011")
        mock_request.state.user_id = user_id
        mock_request.state.username = "testuser"

        # Mock database operations
        user_todos = [
            {
                "_id": ObjectId("507f1f77bcf86cd799439012"),
                "title": "User's Todo 1",
                "description": "First todo",
                "due_date": datetime.now(timezone.utc),
                "priority": "medium",
                "user_id": user_id,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            {
                "_id": ObjectId("507f1f77bcf86cd799439013"),
                "title": "User's Todo 2",
                "description": "Second todo",
                "due_date": datetime.now(timezone.utc),
                "priority": "high",
                "user_id": user_id,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
        ]

        mock_cursor = Mock()
        mock_cursor.limit.return_value = user_todos
        mock_request.app.todo.find.return_value = mock_cursor

        # Get todo list
        result = get_todo_list(mock_request)

        # Verify filtering and results
        mock_request.app.todo.find.assert_called_once_with({"user_id": user_id})
        assert len(result) == 2
        for todo in result:
            assert todo["user_id"] == user_id

    def test_complete_todo_workflow(self, mock_request):
        """Test complete workflow: create todo, then list todos"""
        from app.models.todo import TodoBase
        from app.routers.todo import create_todo, get_todo_list

        # Set up request state (simulating middleware)
        user_id = PyObjectId("507f1f77bcf86cd799439011")
        mock_request.state.user_id = user_id
        mock_request.state.username = "testuser"

        # Step 1: Create a todo
        mock_create_result = Mock()
        mock_create_result.acknowledged = True
        todo_id = ObjectId("507f1f77bcf86cd799439012")
        mock_create_result.inserted_id = todo_id
        mock_request.app.todo.insert_one.return_value = mock_create_result

        todo_data = TodoBase(
            title="Workflow Test Todo",
            description="Testing complete workflow",
            due_date=datetime.now(timezone.utc) + timedelta(seconds=60),
            priority=PriorityEnum.medium,
        )

        created_todo = create_todo(mock_request, todo_data)

        # Verify creation
        assert created_todo.user_id == user_id
        assert created_todo.title == "Workflow Test Todo"

        # Step 2: List todos (should include the created todo)
        created_todo_dict = {
            "_id": todo_id,
            "title": "Workflow Test Todo",
            "description": "Testing complete workflow",
            "due_date": created_todo.due_date,
            "priority": "medium",
            "user_id": user_id,
            "created_at": created_todo.created_at,
            "updated_at": created_todo.updated_at
        }

        mock_cursor = Mock()
        mock_cursor.limit.return_value = [created_todo_dict]
        mock_request.app.todo.find.return_value = mock_cursor

        todos = get_todo_list(mock_request)

        # Verify the created todo appears in the list
        assert len(todos) == 1
        assert todos[0]["_id"] == todo_id
        assert todos[0]["user_id"] == user_id
        assert todos[0]["title"] == "Workflow Test Todo"

        # Verify the list query filtered by user_id
        mock_request.app.todo.find.assert_called_with({"user_id": user_id})

    def test_user_isolation(self, mock_request):
        """Test that users can only see their own todos"""
        from app.routers.todo import get_todo_list

        # Set up request state for user 1
        user1_id = PyObjectId("507f1f77bcf86cd799439011")
        user2_id = PyObjectId("507f1f77bcf86cd799439022")
        mock_request.state.user_id = user1_id
        mock_request.state.username = "user1"

        # Mock database to return only user1's todos
        user1_todos = [
            {
                "_id": ObjectId("507f1f77bcf86cd799439012"),
                "title": "User1's Todo",
                "description": "Belongs to user1",
                "due_date": datetime.now(timezone.utc),
                "priority": "medium",
                "user_id": user1_id,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
        ]

        mock_cursor = Mock()
        mock_cursor.limit.return_value = user1_todos
        mock_request.app.todo.find.return_value = mock_cursor

        # Get todos for user1
        result = get_todo_list(mock_request)

        # Verify only user1's todos are returned
        mock_request.app.todo.find.assert_called_once_with({"user_id": user1_id})
        assert len(result) == 1
        assert result[0]["user_id"] == user1_id
        assert result[0]["user_id"] != user2_id

        # Verify the query specifically filters by user1's ID
        call_args = mock_request.app.todo.find.call_args[0][0]
        assert call_args["user_id"] == user1_id

    @pytest.mark.asyncio
    async def test_middleware_skips_public_endpoints(self):
        """Test that middleware skips processing for public endpoints"""
        public_endpoints = [
            "/token",
            "/docs",
            "/openapi.json",
            "/",
            "/token/refresh",
            "/health",
        ]

        for endpoint in public_endpoints:
            request = Mock(spec=Request)
            request.url.path = endpoint
            # Don't create state attribute initially
            request.state = None

            call_next_called = False

            async def mock_call_next(request):
                nonlocal call_next_called
                call_next_called = True
                # For public endpoints, state should not be modified
                return Mock(status_code=200)

            response = await add_user_info_to_request(request, mock_call_next)
            assert response.status_code == 200
            assert call_next_called, f"call_next should be called for public endpoint {endpoint}"
