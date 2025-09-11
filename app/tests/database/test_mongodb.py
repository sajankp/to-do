import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pymongo.collection import Collection

from app.config import get_settings
from app.database.mongodb import get_todo_collection, get_user_collection

app = FastAPI()


client = TestClient(app)


class TestMongoCollections:
    def setup_method(self, method):
        # Default test values
        self.test_database = "test_database"
        self.test_user_collection = "test_collection"
        self.test_todo_collection = "test_collection"

    def set_env(
        self, monkeypatch, database, user_collection=None, todo_collection=None
    ):
        monkeypatch.setenv("MONGO_DATABASE", database)
        if user_collection:
            monkeypatch.setenv("MONGO_USER_COLLECTION", user_collection)
        if todo_collection:
            monkeypatch.setenv("MONGO_TODO_COLLECTION", todo_collection)

    def get_settings_with_env(
        self, monkeypatch, database, user_collection=None, todo_collection=None
    ):
        self.set_env(monkeypatch, database, user_collection, todo_collection)
        return get_settings()

    def test_returns_collection_object(self, monkeypatch):
        settings = self.get_settings_with_env(
            monkeypatch, self.test_database, user_collection=self.test_user_collection
        )
        collection = get_user_collection(settings)
        assert isinstance(collection, Collection)

    def test_returns_correct_database(self, monkeypatch):
        settings = self.get_settings_with_env(
            monkeypatch, self.test_database, user_collection=self.test_user_collection
        )
        collection = get_user_collection(settings)
        assert collection.database.name == self.test_database

    def test_returns_correct_collection_name(self, monkeypatch):
        settings = self.get_settings_with_env(
            monkeypatch, self.test_database, user_collection=self.test_user_collection
        )
        collection = get_user_collection(settings)
        assert collection.name == self.test_user_collection

    def test_uses_environment_variables(self, monkeypatch):
        settings = self.get_settings_with_env(
            monkeypatch, self.test_database, todo_collection=self.test_todo_collection
        )
        collection = get_todo_collection(settings)
        assert collection.database.name == self.test_database
        assert collection.name == self.test_todo_collection
