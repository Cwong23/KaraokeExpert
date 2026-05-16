import boto3
import os
from pymongo import MongoClient

DOCKER = os.getenv("IS_DOCKER") == "true"

# minio
MINIO_ROOT_USER = os.environ["MINIO_ROOT_USER"]
MINIO_ROOT_PASSWORD = os.environ["MINIO_ROOT_PASSWORD"]
MINIO_ENDPOINT = os.environ["ENDPOINT_URL"]

# Mongo
MONGO_ROOT_USER = os.environ["MONGO_ROOT_USER"]
MONGO_ROOT_PASSWORD = os.environ["MONGO_ROOT_PASSWORD"]
MONGO_DB_NAME = os.environ["MONGO_DB_NAME"]
MONGO_PORT = os.getenv("MONGO_PORT", "27017")
MONGO_HOST = "mongodb" if DOCKER else "localhost"


def container_client():
    s3 = boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ROOT_USER,
        aws_secret_access_key=MINIO_ROOT_PASSWORD,
    )

    yield s3


def mongo_client():
    client = MongoClient(
        f"mongodb://{MONGO_ROOT_USER}:{MONGO_ROOT_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/?authSource=admin")
    db = client[MONGO_DB_NAME]
    return db
