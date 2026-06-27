import json


def process(redis_client, kafka_client, user_id: str, request: dict[str, str]):
    redis_client.set(f"task:{request['song_id']}:status", "processing")
    payload = {"song_id": request["song_id"], "user_id": user_id}

    kafka_client.produce(
        topic='song-processing',
        key=user_id,
        value=json.dumps(payload).encode('utf-8'),
    )

    kafka_client.flush()

    return {}
