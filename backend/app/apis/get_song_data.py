def song_data(collection, user_id: str, song_id: str):
    song = collection.find_one(
        {"userId": user_id, "_id": song_id},
        {"_id": 0}
    )
    return {"song": song}
