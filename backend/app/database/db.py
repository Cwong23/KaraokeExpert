import os
from pymongo import MongoClient
from dotenv import load_dotenv

root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
load_dotenv(os.path.join(root, ".env.local"))

client = None
db = None

def connectDB():
    global client, db
    if db is not None:
        return db

    uri = os.environ.get("MONGO_URI")
    if not uri:
        raise Exception("MONGO_URI not found in environment variables")

    client = MongoClient(uri)
    db = client["karaokeexpert"]
    return db

def getDB():
    if db is None:
        return connectDB()
    return db