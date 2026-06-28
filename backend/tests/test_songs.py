from unittest.mock import patch
from datetime import datetime, UTC
from backend.app.apis.create_upload import get_url
from backend.app.apis.get_completed_songs import completed_songs
from backend.app.apis.get_processing_songs import processing_songs


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
    user_id = "test_user_123"
    request_data = {"song_name": "still"}

    mock_minio_client.generate_presigned_url.return_value = {
        "some.url.test"
    }

    response = get_url(
        minio_client=mock_minio_client,
        collection=test_db.songs,
        user_id=user_id,
        request=request_data,
        redis_client=mock_redis_client
    )

    inserted_song = test_db.songs.find_one({"userId": user_id})

    assert inserted_song
    assert inserted_song["title"] == "still"
    assert inserted_song["status"] == "processing"
    assert f"{user_id}/" in inserted_song["filePath"]
    assert inserted_song["_id"] == response["song_id"]
    assert "url" in response


def test_song_process_route(client, auth_headers, monkeypatch, mock_kafka_client):
    def mock_process_song(redis_client, kafka_client, user_id, request):
        return {}, 200

    monkeypatch.setattr(
        "backend.app.routes.songs.process",
        mock_process_song
    )

    response = client.put(
        '/songs/process_song',
        headers=auth_headers,
        json={'song_id': '1205349f-4d31-4a06-99a9-f3e2aa0b6d9b'}
    )

    assert response.status_code == 200
    assert response.get_json() == {}


def test_get_song_status_route(client, auth_headers, monkeypatch):
    def mock_get_status(redis_client, song_id):
        return {"status": "complete"}, 200

    monkeypatch.setattr(
        "backend.app.routes.songs.get_status",
        mock_get_status
    )

    response = client.get(
        '/songs/1205349f-4d31-4a06-99a9-f3e2aa0b6d9b/song_status',
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.get_json() == {"status": "complete"}


def generate_base_song(user: str):
    now = datetime.now(UTC)
    return {
        "userId": user,
        "title": "Test Song",
        "filePath": f"{user}/songs/song_1/",
        "instrumentalPath": None,
        "vocalPath": None,
        "duration": None,
        "language": None,
        "uploadedAt": now,
    }


def test_completed_songs(test_db):
    user_id_1 = "Chris"
    user_id_2 = "Kyle"
    collection = test_db["songs"]

    base_song_1 = generate_base_song(user_id_1)
    base_song_2 = generate_base_song(user_id_2)

    collection.insert_many([
        {**base_song_1, "_id": "song_1", "title": "Still", "status": "complete"},
        {**base_song_1, "_id": "song_2", "title": "Zzz", "status": "complete"},
        {**base_song_1, "_id": "song_3", "title": "TEAM", "status": "processing"},
        {**base_song_1, "_id": "song_4",
            "title": "Paris, Teargas", "status": "complete"},
        {**base_song_1, "_id": "song_5",
            "title": "Ghost in the Shell", "status": "complete"},
        {**base_song_1, "_id": "song_6", "title": "True", "status": "complete"},
        {**base_song_1, "_id": "song_7", "title": "5ever", "status": "processing"},
        {**base_song_2, "_id": "song_8",
            "title": "Light Sleeper", "status": "complete"},
        {**base_song_2, "_id": "song_9",
            "title": "(Cold Water freestyle)", "status": "complete"},
        {**base_song_2, "_id": "song_10",
            "title": "gggiiiiirrrrlllll", "status": "complete"},
        {**base_song_2, "_id": "song_11", "title": "At Once", "status": "processing"},
        {**base_song_2, "_id": "song_12",
            "title": "Pocket (montreal)", "status": "complete"},
        {**base_song_2, "_id": "song_13", "title": "Quantuuuum", "status": "complete"},
    ])

    response_1 = completed_songs(collection, user_id_1)
    response_2 = completed_songs(collection, user_id_2)

    assert len(response_1["song_ids"]) == 5
    assert "song_1" in response_1["song_ids"]
    assert "song_2" in response_1["song_ids"]
    assert "song_4" in response_1["song_ids"]
    assert "song_5" in response_1["song_ids"]
    assert "song_6" in response_1["song_ids"]
    assert "song_3" not in response_1["song_ids"]
    assert "song_7" not in response_1["song_ids"]

    assert len(response_2["song_ids"]) == 5
    assert "song_8" in response_2["song_ids"]
    assert "song_9" in response_2["song_ids"]
    assert "song_10" in response_2["song_ids"]
    assert "song_12" in response_2["song_ids"]
    assert "song_13" in response_2["song_ids"]
    assert "song_11" not in response_2["song_ids"]
    assert "song_1" not in response_2["song_ids"]


def test_processing_songs(test_db):
    user_id_1 = "Chris"
    user_id_2 = "Kyle"
    collection = test_db["songs"]

    base_song_1 = generate_base_song(user_id_1)
    base_song_2 = generate_base_song(user_id_2)

    collection.insert_many([
        {**base_song_1, "_id": "song_1", "title": "Still", "status": "processing"},
        {**base_song_1, "_id": "song_2", "title": "Zzz", "status": "processing"},
        {**base_song_1, "_id": "song_3", "title": "TEAM", "status": "complete"},
        {**base_song_1, "_id": "song_4",
            "title": "Paris, Teargas", "status": "processing"},
        {**base_song_1, "_id": "song_5",
            "title": "Ghost in the Shell", "status": "complete"},
        {**base_song_2, "_id": "song_6",
            "title": "Light Sleeper", "status": "processing"},
        {**base_song_2, "_id": "song_7",
            "title": "(Cold Water freestyle)", "status": "processing"},
        {**base_song_2, "_id": "song_8",
            "title": "gggiiiiirrrrlllll", "status": "complete"},
        {**base_song_2, "_id": "song_9", "title": "At Once", "status": "processing"},
        {**base_song_2, "_id": "song_10",
            "title": "Pocket (montreal)", "status": "complete"},
    ])

    response_1 = processing_songs(collection, user_id_1)
    response_2 = processing_songs(collection, user_id_2)

    assert len(response_1["song_ids"]) == 3
    assert "song_1" in response_1["song_ids"]
    assert "song_2" in response_1["song_ids"]
    assert "song_4" in response_1["song_ids"]
    assert "song_3" not in response_1["song_ids"]
    assert "song_5" not in response_1["song_ids"]

    assert len(response_2["song_ids"]) == 3
    assert "song_6" in response_2["song_ids"]
    assert "song_7" in response_2["song_ids"]
    assert "song_9" in response_2["song_ids"]
    assert "song_8" not in response_2["song_ids"]
    assert "song_10" not in response_2["song_ids"]
    assert "song_1" not in response_2["song_ids"]
