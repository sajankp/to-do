import asyncio
import logging
import os
import sys
import urllib

from dotenv import load_dotenv
from fastapi import FastAPI
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

app = FastAPI()

load_dotenv()

password = urllib.parse.quote(os.getenv("MONGO_PASSWORD"), safe="")
username = urllib.parse.quote(os.getenv("MONGO_USERNAME"), safe="")
uri = f"mongodb+srv://{username}:{password}@cluster0.gbaxrnp.mongodb.net/?retryWrites=true&w=majority"
TIMEOUT = int(os.getenv("MONGO_TIMEOUT", 5))


def get_mongo_client(server_selection_timeout_ms=TIMEOUT*1000):
    client = MongoClient(uri, serverSelectionTimeoutMS=server_selection_timeout_ms)
    return client


async def check_app_readiness(max_attempts=3, timeout=TIMEOUT/1000):
    # Add your own readiness check logic here
    # For example, you can check if the necessary resources are available or if certain conditions are met
    attempts = 0
    while attempts < max_attempts:
        try:
            logging.info(f"Attempting readiness check. Attempt #{attempts + 1}")
            mongo_client = get_mongo_client()
            mongo_client.admin.command("ping")
            return True
        except ServerSelectionTimeoutError as e:
            logging.warning(f"Readiness check failed. Attempt #{attempts + 1}. Error: {str(e)}")
            attempts += 1
            await asyncio.sleep(1)
    logging.error(f"Application failed to start after {max_attempts} attempts.")
    return False


@app.on_event("startup")
async def startup():
    # Wait for the application to be ready before continuing
    if not await check_app_readiness():
        logging.error("Application failed to start.")
        sys.exit(1)
    app.mongodb_client = get_mongo_client()


@app.on_event("shutdown")
async def shutdown():
    if hasattr(app, "mongodb_client"):
        app.mongodb_client.close()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/health")
def check_health():
    try:
        if hasattr(app, "mongodb_client"):
            app.mongodb_client.admin.command("ping")
            return {"status": "OK"}
        else:
            return {"status": "Error", "error": "MongoDB client not initialized"}
    except Exception as e:
        return {"status": "Error", "error": str(e)}
