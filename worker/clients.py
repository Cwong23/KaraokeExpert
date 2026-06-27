import boto3
import os
from pymongo import MongoClient
from redis import Redis
from botocore.config import Config
from functools import lru_cache
import json
import logging
import signal
import sys
from confluent_kafka import Consumer, KafkaError

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

logger = logging.getLogger("KafkaQueue")


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
def db_client():
    client = MongoClient(
        f"mongodb://{MONGO_ROOT_USER}:{MONGO_ROOT_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/?authSource=admin")
    db = client[MONGO_DB_NAME]
    return db


@lru_cache(maxsize=1)
def status_client():
    client = Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        decode_responses=True
    )
    return client


class KafkaQueueConsumer:
    def __init__(self, bootstrap_servers: str, group_id: str):
        """Initializes a dedicated Kafka Queue Consumer Client."""
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.consumer = None
        self._shutdown_requested = False

        self.config = {
            "bootstrap.servers": self.bootstrap_servers,
            "group.id": self.group_id,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,  # Manual commits only on successful stem separation
            "max.poll.interval.ms": 600000
        }

    def start_worker(self, topic: str, task_handler_callback):
        """
        Connects to the broker and spins up the infinite task polling worker loop.
        """
        self.consumer = Consumer(self.config)
        self.consumer.subscribe([topic])
        logger.info(
            f"Worker connected. Polling '{topic}' under consumer group '{self.group_id}'...")

        # Setup OS signal traps for graceful teardown
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

        try:
            while not self._shutdown_requested:
                msg = self.consumer.poll(timeout=1.0)
                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        logger.error(
                            f"Kafka Wire Protocol Error: {msg.error()}")
                        continue

                self._process_message(msg, task_handler_callback)

        finally:
            self._close_connection()

    def _process_message(self, msg, callback):
        """Deserializes message data blocks and calls the target processing script."""
        try:
            raw_data = msg.value().decode("utf-8")
            task = json.loads(raw_data)

            logger.info(f"Processing task event: {task.get('task_type')}")

            success = callback(task)

            if success:
                self.consumer.commit(message=msg, asynchronous=False)
                logger.info("Task acknowledged and committed successfully.")
            else:
                logger.warning(
                    "Core execution returned False. Task offset was NOT committed.")

        except Exception as err:
            logger.error(
                f"Uncaught exception handling payload block: {err}", exc_info=True)

    def _handle_shutdown(self, sig, frame):
        """Intercepts kill signals to allow workers to exit cleanly."""
        logger.info(
            "Shutdown signal caught. Completing current task before close...")
        self._shutdown_requested = True

    def _close_connection(self):
        """Closes sockets and leaves the consumer cluster group cleanly."""
        if self.consumer:
            logger.info("Closing active Kafka cluster connection channels...")
            self.consumer.close()
        sys.exit(0)


@lru_cache(maxsize=1)
def queue_client():
    client = KafkaQueueConsumer(
        bootstrap_servers=os.environ["KAFKA_BOOTSTRAP_SERVERS"],
        group_id="karaoke-queue"
    )
    return client
