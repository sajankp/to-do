import asyncio
import logging

from pymongo.errors import ServerSelectionTimeoutError

from app.database.mongodb import get_mongo_client


def app_check_health(app):
    try:
        if hasattr(app, "mongodb_client"):
            app.mongodb_client.admin.command("ping")
            return {"status": "OK"}
        else:
            return {"status": "Error", "error": "MongoDB client not initialized"}
    except Exception as e:
        return {"status": "Error", "error": str(e)}


async def check_app_readiness(max_attempts=3, timeout=1):
    # Add your own readiness check logic here
    # For example, you can check if the necessary resources are available or if certain conditions are met
    attempts = 0
    while attempts < max_attempts:
        try:
            logging.info(f"Attempting readiness check. Attempt #{attempts + 1}")
            mongo_client = get_mongo_client()
            mongo_client.admin.command("ping", timeout)
            return True
        except ServerSelectionTimeoutError as e:
            logging.warning(f"Readiness check failed. Attempt #{attempts + 1}. Error: {str(e)}")
            attempts += 1
            await asyncio.sleep(timeout)
    logging.error(f"Application failed to start after {max_attempts} attempts.")
    return False
