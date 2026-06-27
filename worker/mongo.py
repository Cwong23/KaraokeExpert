import os
from pymongo import MongoClient

# Mongo
MONGO_ROOT_USER = os.environ["MONGO_ROOT_USER"]
MONGO_ROOT_PASSWORD = os.environ["MONGO_ROOT_PASSWORD"]
MONGO_DB_NAME = os.environ["MONGO_DB_NAME"]
MONGO_PORT = os.getenv("MONGO_PORT", "27017")
MONGO_HOST = os.getenv("MONGO_HOST")


def mongo_client():
    client = MongoClient(
        f"mongodb://{MONGO_ROOT_USER}:{MONGO_ROOT_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/?authSource=admin")
    db = client[MONGO_DB_NAME]
    return db
