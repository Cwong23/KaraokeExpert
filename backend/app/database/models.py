from datetime import datetime, UTC
import bcrypt


def new_user(email: str, password: str) -> dict:
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return {
        "email": email,
        "password": hashed,
        "createdAt": datetime.utcnow(),
    }


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
        "status": "processing",
        "uploadedAt": datetime.now(UTC),
    }
