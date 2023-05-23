import os
import urllib
from dotenv import load_dotenv
from fastapi import FastAPI
from pymongo import MongoClient

app = FastAPI()

load_dotenv()

password = urllib.parse.quote(os.getenv("MONGO_PASSWORD"), safe="")
username = urllib.parse.quote(os.getenv("MONGO_USERNAME"), safe="")
uri = f"mongodb+srv://{username}:{password}@cluster0.gbaxrnp.mongodb.net/?retryWrites=true&w=majority"


def get_mongo_client():
    client = MongoClient(uri)
    return client


@app.on_event("startup")
async def startup():
    app.mongodb_client = get_mongo_client()


@app.on_event("shutdown")
async def shutdown():
    app.mongodb_client.close()


@app.get("/")
def read_root():
    return {"Hello": "World"}

