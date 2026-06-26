import boto3
import os
from botocore.config import Config

DOCKER = os.getenv("IS_DOCKER") == "true"

# Minio
MINIO_ROOT_USER = os.environ["MINIO_ROOT_USER"]
MINIO_ROOT_PASSWORD = os.environ["MINIO_ROOT_PASSWORD"]
MINIO_ENDPOINT = "http://minio:9000"  # os.environ["ENDPOINT_URL"]
MINIO_BUCKET_NAME = os.environ["MINIO_BUCKET_NAME"]


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
