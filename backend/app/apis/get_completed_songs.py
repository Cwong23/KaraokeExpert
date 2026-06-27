def get_completed_songs(collection, user_id: str):
    songs = list(collection.find(
        {"userId": user_id, "status": "complete"},
        {"_id": 0}
    ))

    return {"song_ids": [s["song_id"] for s in songs]}
