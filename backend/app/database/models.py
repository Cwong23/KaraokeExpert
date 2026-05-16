from datetime import datetime, UTC
from bson import ObjectId


def new_song(song_id: str, user_id: str, title: str, file_path: str) -> dict:
    return {
        "_id": song_id,
        "userId": user_id,
        "title": title,
        "filePath": file_path,
        "instrumentalPath": None,
        "vocalPath": None,
        "duration": None,
        "language": None,
        "status": "uploading",
        "uploadedAt": datetime.now(UTC),
    }


def new_lyrics(song_id, language: str, lines: list) -> dict:
    return {
        "songId": song_id,
        "language": language,
        # list of dictionaries, each dictionary containing text, start time, and end time
        "lines": lines,
        "createdAt": datetime.now(UTC),
    }


def new_pitch_session(user_id: str, song_id, artist_pitch: list, user_pitch: list, accuracy_score: float) -> dict:
    return {
        "userId": user_id,
        "songId": song_id,
        "artistPitch": artist_pitch,
        "userPitch": user_pitch,
        "accuracyScore": accuracy_score,  # final score displayed at end
        "createdAt": datetime.now(UTC),
    }
