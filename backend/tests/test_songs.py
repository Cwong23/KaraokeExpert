from unittest.mock import patch
from backend.app.apis.create_multipart_upload import create_upload


def test_no_auth_song(client):
    response = client.post('/songs/create_upload')

    assert response.status_code == 401


def test_song_upload_route(client, auth_headers, monkeypatch):
    def mock_create_upload(minio_client, collection, user_id, request):
        return {"upload_id": "mock-upload-id-123", "song_id": "id"}, 200

    monkeypatch.setattr(
        "backend.app.routes.songs.create_upload",
        mock_create_upload
    )

    response = client.post(
        '/songs/create_upload',
        headers=auth_headers,
        json={'song_name': 'still'}
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "upload_id": "mock-upload-id-123", "song_id": "id"}


def test_song_upload(mock_minio_client, test_db_client, test_db):
    collection = test_db["songs"]
    user_id = "test_user_123"
    request_data = {"song_name": "still"}

    mock_minio_client.create_multipart_upload.return_value = {
        "UploadId": "banana"
    }

    response = create_upload(
        minio_client=mock_minio_client,
        collection=collection,
        user_id=user_id,
        request=request_data
    )

    inserted_song = collection.find_one({"userId": user_id})

    assert inserted_song
    assert inserted_song["title"] == "still"
    assert inserted_song["status"] == "uploading"
    assert f"{user_id}/" in inserted_song["filePath"]
    assert inserted_song["_id"] == response["song_id"]
    assert response["upload_id"] == "banana"
