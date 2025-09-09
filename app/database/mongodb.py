from pymongo import MongoClient
from app.config import settings

uri = (
    f"mongodb+srv://{settings.mongo_username}:"
    f"{settings.mongo_password}@{settings.mongo_host}/?retryWrites=true&w=majority"
)
TIMEOUT = 5  # You can add this to config.py if needed


mongodb_client = get_mongo_client()
def get_todo_collection():
def get_user_collection():
def get_mongo_client(server_selection_timeout_ms=TIMEOUT * 1000):
    client = MongoClient(uri, serverSelectionTimeoutMS=server_selection_timeout_ms)
    return client

mongodb_client = get_mongo_client()

def get_todo_collection():
    database = mongodb_client[settings.mongo_db]
    return database[settings.mongo_todo_collection]

def get_user_collection():
    database = mongodb_client[settings.mongo_db]
    return database[settings.mongo_user_collection]
