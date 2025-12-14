import os
from unittest.mock import Mock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import app, lifespan

client = TestClient(app)
mongodb_client = Mock()


@pytest.fixture(autouse=True)
def set_env_vars():
    os.environ["MONGO_PASSWORD"] = "your_password"
    os.environ["MONGO_USER"] = "your_user"


@pytest.fixture(scope="module")
def test_client():
    # Setup code (runs once for the entire module)
    client = TestClient(app)
    client.mongodb_client = mongodb_client
    print(client, client.mongodb_client)
    # Code to run before the tests
    print("Setting up test client")

    # Yield the client to the tests
    yield client

    # Teardown code (runs once after all tests are done)
    print("Tearing down test client")


def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World!"}


def test_health_endpoint_unauthorized():
    response = client.get("/health")
    assert response.status_code == 401


# Assuming a mock for the MongoDB client is available
os.environ["MONGO_DATABASE"] = "test_database"
os.environ["MONGO_TODO_COLLECTION"] = "todo"
os.environ["MONGO_USER_COLLECTION"] = "user"

app = FastAPI()


@pytest.mark.asyncio
@patch("app.main.mongodb_client")
@patch("app.main.check_app_readiness")
async def test_lifespan_with_fastapi_instance(mock_check_app_readiness, mock_mongodb_client):
    mock_database = Mock(side_effect=lambda name: Mock(name=f"MockCollection-{name}"))
    mock_mongodb_client.return_value = mock_database
    mock_check_app_readiness.return_value = True

    async with lifespan(app) as _:
        assert app.mongodb_client is mock_mongodb_client
        assert app.todo == app.database["todo"]
        assert app.user == app.database["user"]

    # Ensure MongoDB client is closed after the context manager exits
    assert mock_mongodb_client.close.called
