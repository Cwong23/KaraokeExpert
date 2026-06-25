import os
from redis import Redis

# Redis
REDIS_HOST = os.environ["REDIS_HOST"]
REDIS_PORT = os.environ["REDIS_PORT"]


def redis_client():
    client = Redis(host=REDIS_HOST, port=REDIS_PORT,
                   db=0, decode_responses=True)
    yield client
