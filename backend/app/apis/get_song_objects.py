import os
from http import HTTPStatus


def get_url(minio_client, user_id: str, song_id: str):
    file_path = f"{user_id}/{song_id}/"
    urls = []

    for key in ["instrumental.wav", "vocals.wav", "pitches.json", "lyrics.json"]:
        url = minio_client.generate_presigned_url(
            Bucket=os.environ["MINIO_BUCKET_NAME"],
            Key=file_path + key
        )
        urls.append(url)

    return {"urls": urls}
