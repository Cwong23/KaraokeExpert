def processing_songs(collection, user_id: str):
    songs = list(collection.find(
        {"user_id": user_id, "status": "processing"},
        {"_id": 0, "song_id": 1}
    ))

    return {"song_ids": [s["song_id"] for s in songs]}
