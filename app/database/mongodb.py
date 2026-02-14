from pymongo import MongoClient

from app.config import Settings, get_settings


def get_mongo_client(settings: Settings | None = None):
    if settings is None:
        settings = get_settings()

    # Use direct URI if provided, otherwise construct from parts
    if settings.mongo_uri:
        uri = settings.mongo_uri
    else:
        uri = (
            f"mongodb+srv://{settings.mongo_username}:"
            f"{settings.mongo_password}@{settings.mongo_host}/?retryWrites=true&w=majority"
        )

    timeout = settings.mongo_timeout or 5
    server_selection_timeout_ms = timeout * 1000
    client = MongoClient(uri, serverSelectionTimeoutMS=server_selection_timeout_ms)
    return client


def get_todo_collection(client: MongoClient, settings: Settings | None = None):
    """Get todo collection using the provided MongoDB client.

    Args:
        client: MongoDB client instance (should be the instrumented client from app state)
        settings: Optional settings, will use default if not provided
    """
    if settings is None:
        settings = get_settings()
    database = client[settings.mongo_db]
    return database[settings.mongo_todo_collection]


def get_user_collection(client: MongoClient, settings: Settings | None = None):
    """Get user collection using the provided MongoDB client.

    Args:
        client: MongoDB client instance (should be the instrumented client from app state)
        settings: Optional settings, will use default if not provided
    """
    if settings is None:
        settings = get_settings()
    database = client[settings.mongo_db]
    return database[settings.mongo_user_collection]
