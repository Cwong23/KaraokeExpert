def get_song_data(collection, user_id: str, song_id: str):
    song = collection.find_one(
        {"user_id": user_id, "song_id": song_id},
        {"_id": 0}
    )

    return song
