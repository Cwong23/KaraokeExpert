from unittest.mock import patch
from backend.app.apis.create_upload import get_url
from backend.app.apis.process_song import process


def test_no_auth_song(client):
    response = client.post('/songs/create_upload')
    assert response.status_code == 401

    response = client.put('/songs/process_song')
    assert response.status_code == 401


def test_song_upload_route(client, auth_headers, monkeypatch):
    def mock_get_url(minio_client, redis_client, collection, user_id, request):
        return {"url": "test-url", "song_id": "id"}, 200

    monkeypatch.setattr(
        "backend.app.routes.songs.get_url",
        mock_get_url
    )

    response = client.post(
        '/songs/create_upload',
        headers=auth_headers,
        json={'song_name': 'still'}
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "url": "test-url", "song_id": "id"}


def test_song_upload(mock_minio_client, test_db_client, test_db, mock_redis_client):
    collection = test_db["songs"]
    user_id = "test_user_123"
    request_data = {"song_name": "still"}

    mock_minio_client.create_multipart_upload.return_value = {
        "UploadId": "banana"
    }

    response = get_url(
        minio_client=mock_minio_client,
        collection=collection,
        user_id=user_id,
        request=request_data,
        redis_client=mock_redis_client
    )

    inserted_song = collection.find_one({"userId": user_id})

    assert inserted_song
    assert inserted_song["title"] == "still"
    assert inserted_song["status"] == "uploading"
    assert f"{user_id}/" in inserted_song["filePath"]
    assert inserted_song["_id"] == response["song_id"]
    assert "url" in response


def test_song_process_route(client, auth_headers, monkeypatch, mock_kafka_client, ):
    def mock_process_song(redis_client, kafka_client, user_id, request):
        return {}, 200

    monkeypatch.setattr(
        "backend.app.routes.songs.process",
        mock_process_song
    )

    response = client.put(
        '/songs/process_song',
        headers=auth_headers,
        json={'song_id': '123'}
    )

    assert response.status_code == 200
    assert response.get_json() == {}
