from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.base import PyObjectId


@pytest.fixture
def mock_mongo_client():
    """
    Shared fixture to mock the MongoDB client.
    Using MagicMock allows subscripting (client['db_name']).
    """
    mock_client = MagicMock()
    # Ensure client[db][collection] returns a MagicMock
    mock_db = MagicMock()
    mock_client.__getitem__.return_value = mock_db
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection

    return mock_client


@pytest.fixture(autouse=True)
def patch_mongo_client(mock_mongo_client):
    """
    Automatically patch the app.mongodb_client for all tests
    to prevent "Mock object is not subscriptable" errors.
    """
    # Patch the client on the app instance
    app.mongodb_client = mock_mongo_client
    # Also patch the specific collections to be children of this client
    # This keeps the mock hierarchy consistent
    app.database = mock_mongo_client["test_db"]
    app.user = app.database["users"]
    app.todo = app.database["todos"]

    yield

    # Optional cleanup if needed, but app is global so maybe not


@pytest.fixture
def client():
    """
    Shared TestClient fixture.
    """

    return TestClient(app)


@pytest.fixture
def mock_user_id():
    """
    Shared mock user ID.
    """

    return PyObjectId("507f1f77bcf86cd799439011")
