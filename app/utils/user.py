from app.database.mongodb import get_user_collection
from app.models.user import UserInDB


def get_user_by_username(username: str) -> UserInDB | None:
    """
    Fetch a user from the database by username.

    Args:
        username: The username to search for.

    Returns:
        UserInDB if found, None otherwise.
    """
    user_collection = get_user_collection()
    return user_collection.find_one({"username": username})
