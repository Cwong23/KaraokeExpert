import json
from http import HTTPStatus


def get_status(redis_client, song_id: str):
    status = redis_client.get(f"task:{song_id}:status")
    return {"status": status}
