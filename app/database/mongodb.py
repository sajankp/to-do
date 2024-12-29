import os
import urllib

from dotenv import load_dotenv
from pymongo import MongoClient

if os.getenv("TESTING", "0") == "0":
    pass
else:
    load_dotenv()

password = urllib.parse.quote(os.getenv("MONGO_PASSWORD"), safe="")
username = urllib.parse.quote(os.getenv("MONGO_USERNAME"), safe="")
uri = f"mongodb+srv://{username}:{password}@cluster0.gbaxrnp.mongodb.net/?retryWrites=true&w=majority"
TIMEOUT = int(os.getenv("MONGO_TIMEOUT", 5))


def get_mongo_client(server_selection_timeout_ms=TIMEOUT * 1000):
    client = MongoClient(uri, serverSelectionTimeoutMS=server_selection_timeout_ms)
    return client


mongodb_client = get_mongo_client()


def get_todo_collection():
    database = mongodb_client[os.getenv("MONGO_DATABASE")]
    return database[os.getenv("MONGO_TODO_COLLECTION")]


def get_user_collection():
    database = mongodb_client[os.getenv("MONGO_DATABASE")]
    return database[os.getenv("MONGO_USER_COLLECTION")]
