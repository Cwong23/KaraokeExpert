import os
from http import HTTPStatus
from app.database.models import new_song
import uuid


def create_upload(minio_client, collection, user_id: str, request: dict[str, str]):
    song_id = str(uuid.uuid4())
    file_path = f"{user_id}/{song_id}/"

    song_document = new_song(
        user_id=user_id, song_id=song_id, title=request["song_name"], file_path=f"{user_id}/{song_id}/")

    collection.insert_one(song_document)

    response = minio_client.create_multipart_upload(
        Bucket=os.environ["MINIO_BUCKET_NAME"],
        Key=file_path + "original.wav"
    )

    upload_id = response['UploadId']

    return {"upload_id": upload_id, "song_id": song_id}
