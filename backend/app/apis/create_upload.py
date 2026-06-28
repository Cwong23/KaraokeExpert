import os
from backend.app.database.models import new_song
from uuid import uuid4


def get_url(minio_client, redis_client, collection, user_id: str, request: dict[str, str]):
    uuid = str(uuid4())
    file_path = f"{user_id}/songs/{uuid}/"

    song_document = new_song(
        user_id=user_id, song_id=uuid, title=request["song_name"], file_path=f"{user_id}/songs/{uuid}/")

    collection.insert_one(song_document)

    url = minio_client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": os.environ["MINIO_BUCKET_NAME"],
            "Key": file_path + "original.wav",
        },
        ExpiresIn=3600
    )

    redis_client.set(f"task:{uuid}:status", "creating")

    return {"url": url, "song_id": uuid}
