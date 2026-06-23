import json
from http import HTTPStatus


def get_status(redis_client, request: dict[str, str]):
    status = redis_client.get(f"task:{request['song_id']}:status")
    return {"status": status}
