from confluent_kafka import Producer
import boto3
import os
from pymongo import MongoClient
from redis import Redis
from botocore.config import Config
from functools import lru_cache

# Minio
MINIO_ROOT_USER = os.environ["MINIO_ROOT_USER"]
MINIO_ROOT_PASSWORD = os.environ["MINIO_ROOT_PASSWORD"]
MINIO_ENDPOINT = os.environ["ENDPOINT_URL"]

# Mongo
MONGO_ROOT_USER = os.environ["MONGO_ROOT_USER"]
MONGO_ROOT_PASSWORD = os.environ["MONGO_ROOT_PASSWORD"]
MONGO_DB_NAME = os.environ["MONGO_DB_NAME"]
MONGO_PORT = os.environ["MONGO_PORT"]
MONGO_HOST = os.environ["MONGO_HOST"]

# Redis
REDIS_HOST = os.environ["REDIS_HOST"]
REDIS_PORT = os.environ["REDIS_PORT"]
REDIS_PASSWORD = os.environ["REDIS_PASSWORD"]

# Kafka
KAFKA_PORT = os.environ["KAFKA_PORT"]


@lru_cache(maxsize=1)
def container_client():
    s3 = boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ROOT_USER,
        aws_secret_access_key=MINIO_ROOT_PASSWORD,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )
    return s3


@lru_cache(maxsize=1)
def mongo_client():
    client = MongoClient(
        f"mongodb://{MONGO_ROOT_USER}:{MONGO_ROOT_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/?authSource=admin")
    db = client[MONGO_DB_NAME]
    return db


@lru_cache(maxsize=1)
def redis_client():
    client = Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        decode_responses=True
    )
    return client


@lru_cache(maxsize=1)
def kafka_client():
    return Producer({'bootstrap.servers': f'kafka:{KAFKA_PORT}'})
