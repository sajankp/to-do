from pymongo import MongoClient

from app.database.mongodb import get_user_collection
from app.models.user import UserInDB


def get_user_by_username(username: str, client: MongoClient) -> UserInDB | None:
    """
    Fetch a user from the database by username.

    Args:
        username: The username to search for.
        client: MongoDB client instance (must be instrumented client from app)

    Returns:
        UserInDB if found, None otherwise.
    """
    user_collection = get_user_collection(client)
    user_data = user_collection.find_one({"username": username})
    if user_data:
        return UserInDB(**user_data)
    return None
