import os

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pymongo.collection import Collection

from app.config import get_settings
from app.database.mongodb import get_todo_collection, get_user_collection

app = FastAPI()

client = TestClient(app)


def test_returns_collection_object(monkeypatch):
    monkeypatch.setenv("MONGO_DATABASE", "test_database")
    monkeypatch.setenv("MONGO_USER_COLLECTION", "test_collection")
    settings = get_settings()
    collection = get_user_collection(settings)

    assert isinstance(collection, Collection)


def test_returns_correct_database(monkeypatch):
    monkeypatch.setenv("MONGO_DATABASE", "test_database")
    monkeypatch.setenv("MONGO_USER_COLLECTION", "test_collection")
    settings = get_settings()
    collection = get_user_collection(settings)

    assert collection.database.name == "test_database"


def test_returns_correct_collection_name(monkeypatch):
    monkeypatch.setenv("MONGO_DATABASE", "test_database")
    monkeypatch.setenv("MONGO_USER_COLLECTION", "test_collection")
    settings = get_settings()
    collection = get_user_collection(settings)

    assert collection.name == "test_collection"


def test_uses_environment_variables(monkeypatch):
    monkeypatch.setenv("MONGO_DATABASE", "test_database")
    monkeypatch.setenv("MONGO_TODO_COLLECTION", "test_collection")
    settings = get_settings()
    collection = get_todo_collection(settings)
    assert collection.database.name == "test_database"
    assert collection.name == "test_collection"
