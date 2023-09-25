import logging
import os
import sys

from database import get_mongo_client
from fastapi import FastAPI
from routers.todo import router as todo_router
from utils.health import app_check_health, check_app_readiness

app = FastAPI()

app.include_router(todo_router, prefix="/todo", tags=["todo"])


@app.on_event("startup")
async def startup():
    # Wait for the application to be ready before continuing
    if not await check_app_readiness():
        logging.error("Application failed to start.")
        sys.exit(1)
    app.mongodb_client = get_mongo_client()
    app.database = app.mongodb_client[os.getenv("MONGO_DATABASE")]
    app.todo = app.database[os.getenv("MONGO_COLLECTIONS")]


@app.on_event("shutdown")
async def shutdown():
    if hasattr(app, "mongodb_client"):
        app.mongodb_client.close()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/health")
def check_health():
    return app_check_health(app)
