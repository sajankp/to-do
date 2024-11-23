import os

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pymongo.collection import Collection

from app.database.mongodb import get_todo_collection, get_user_collection

app = FastAPI()

client = TestClient(app)


def test_returns_collection_object():
    os.environ["MONGO_DATABASE"] = "test_database"
    os.environ["MONGO_USER_COLLECTION"] = "test_collection"

    collection = get_user_collection()

    assert isinstance(collection, Collection)


def test_returns_correct_database():
    os.environ["MONGO_DATABASE"] = "test_database"
    os.environ["MONGO_USER_COLLECTION"] = "test_collection"

    collection = get_user_collection()

    assert collection.database.name == "test_database"


def test_returns_correct_collection_name():
    os.environ["MONGO_DATABASE"] = "test_database"
    os.environ["MONGO_USER_COLLECTION"] = "test_collection"

    collection = get_user_collection()

    assert collection.name == "test_collection"


def test_uses_environment_variables():
    os.environ["MONGO_DATABASE"] = "test_database"
    os.environ["MONGO_TODO_COLLECTION"] = "test_collection"
    collection = get_todo_collection()
    assert collection.database.name == "test_database"
    assert collection.name == "test_collection"
