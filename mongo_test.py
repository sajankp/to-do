import os
import urllib

from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


load_dotenv()

password = urllib.parse.quote(os.getenv("MONGO_PASSWORD"), safe="")
username = urllib.parse.quote(os.getenv("MONGO_USERNAME"), safe="")
uri = f"mongodb+srv://{username}:{password}@cluster0.gbaxrnp.mongodb.net/?retryWrites=true&w=majority"
# Set the Stable API version when creating a new client
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)
