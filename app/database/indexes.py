import logging

import pymongo
from pymongo import MongoClient

from app.database.mongodb import get_user_collection

logger = logging.getLogger(__name__)


def create_indexes(client: MongoClient) -> None:
    """
    Create indexes for the application collections.
    This function is idempotent and should be called on startup.
    """
    user_collection = get_user_collection(client)

    # Unique index on username
    user_collection.create_index(
        [("username", pymongo.ASCENDING)],
        unique=True,
        background=True,
        name="unique_username",
    )

    # Unique index on email
    user_collection.create_index(
        [("email", pymongo.ASCENDING)],
        unique=True,
        background=True,
        name="unique_email",
    )

    logger.info("Database indexes created successfully.")
