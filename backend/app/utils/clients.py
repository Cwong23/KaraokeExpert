import json
from confluent_kafka import Producer
import boto3
import os
from pymongo import MongoClient
from redis import Redis

DOCKER = os.getenv("IS_DOCKER") == "true"

# Minio
MINIO_ROOT_USER = os.environ["MINIO_ROOT_USER"]
MINIO_ROOT_PASSWORD = os.environ["MINIO_ROOT_PASSWORD"]
MINIO_ENDPOINT = os.environ["ENDPOINT_URL"]

# Mongo
MONGO_ROOT_USER = os.environ["MONGO_ROOT_USER"]
MONGO_ROOT_PASSWORD = os.environ["MONGO_ROOT_PASSWORD"]
MONGO_DB_NAME = os.environ["MONGO_DB_NAME"]
MONGO_PORT = os.getenv("MONGO_PORT", "27017")
MONGO_HOST = os.getenv("MONGO_HOST")

# Redis
REDIS_HOST = os.environ["REDIS_HOST"]
REDIS_PORT = os.environ["REDIS_PORT"]
REDIS_PASSWORD = os.environ["REDIS_PASSWORD"]

# Kafka
KAFKA_PORT = os.environ["KAFKA_PORT"]


def container_client():
    s3 = boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ROOT_USER,
        aws_secret_access_key=MINIO_ROOT_PASSWORD,
    )

    return s3


def mongo_client():
    client = MongoClient(
        f"mongodb://{MONGO_ROOT_USER}:{MONGO_ROOT_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/?authSource=admin")
    db = client[MONGO_DB_NAME]
    return db


def redis_client():
    client = Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        decode_responses=True
    )
    return client


def kafka_client():
    return Producer({'bootstrap.servers': KAFKA_PORT})
