import os

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pymongo.collection import Collection

from app.database.mongodb import get_user_collection

app = FastAPI()

client = TestClient(app)


def test_returns_collection_object():
    os.environ["MONGO_DATABASE"] = "test_database"
    os.environ["MONGO_USER_COLLECTION"] = "test_collection"

    collection = get_user_collection()

    assert isinstance(collection, Collection)
