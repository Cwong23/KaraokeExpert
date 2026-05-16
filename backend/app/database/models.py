from datetime import datetime


# Song
def new_song(user_id: str, title: str, file_path: str) -> dict:
    return {
        "userId": user_id, # connected to clerk
        "title": title,
        "filePath": file_path, # original audio
        "instrumentalPath": None, # instrumental audio
        "vocalPath": None, # just vocals audio
        "duration": None,
        "language": None,
        "status": "uploaded",
        "uploadedAt": datetime.utcnow(),
    }


# Lyrics
def new_lyrics(song_id, language: str, lines: list) -> dict:
    return {
        "songId": song_id,
        "language": language,
        "lines": lines, # list of dictionaries, each dictionary containing text, start time, and end time
        "createdAt": datetime.utcnow(),
    }


# Pitch Session
def new_pitch_session(user_id: str, song_id, artist_pitch: list, user_pitch: list, accuracy_score: float) -> dict:
    return {
        "userId": user_id,
        "songId": song_id,
        "artistPitch": artist_pitch,
        "userPitch": user_pitch,
        "accuracyScore": accuracy_score, # final score displayed at end
        "createdAt": datetime.utcnow(),
    }