def completed_songs(collection, user_id: str):
    songs = list(collection.find(
        {"userId": user_id, "status": "complete"},
    ))
    print("SONGS: ", songs)
    return {"song_ids": [s["_id"] for s in songs]}
