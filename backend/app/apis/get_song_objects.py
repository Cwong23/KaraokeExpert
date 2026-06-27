import os


def get_urls(minio_client, user_id: str, song_id: str):
    file_path = f"{user_id}/{song_id}/"
    urls = []

    for key in ["instrumental.wav", "lyrics.json"]:
        url = minio_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": os.environ["MINIO_BUCKET_NAME"],
                "Key": file_path + key,
            },
            ExpiresIn=3600
        )
        urls.append(url)

    return {"urls": urls}
