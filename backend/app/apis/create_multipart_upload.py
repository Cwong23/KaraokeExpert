import os
from http import HTTPStatus
from backend.app.database.models import new_song
from uuid import uuid6


def create_upload(minio_client, collection, user_id: str, request: dict[str, str]):
    uuid = str(uuid6())
    file_path = f"{user_id}/{uuid}/"

    song_document = new_song(
        user_id=user_id, song_id=uuid, title=request["song_name"], file_path=f"{user_id}/{uuid}/")

    collection.insert_one(song_document)

    response = minio_client.create_multipart_upload(
        Bucket=os.environ["MINIO_BUCKET_NAME"],
        Key=file_path + "original.wav"
    )

    upload_id = response['UploadId']

    return {"upload_id": upload_id, "song_id": uuid}
