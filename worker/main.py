import time
import json
import os
from queue_client import KafkaQueueConsumer
import io
import logging
from separate import Config, separate_audio
from bucket_client import container_client, MINIO_BUCKET_NAME
from speech import transcribe_audio
from redis_client import redis_client
from mongo import mongo_client
import torch
import gc

log = logging.getLogger(__name__)


def process_audio_job(task):
    song_id = task.get("song_id")
    user_id = task.get("user_id")

    minio_client = container_client()
    r_client = redis_client()
    m_client = mongo_client()

    if not song_id or not user_id:
        log.error("Aborting task: Missing essential metadata.")
        return False

    log.info(f"Working on {song_id} for {user_id}")
    vocal_stream, instr_stream = None, None
    try:
        # grab audio
        source_key = f"{user_id}/songs/{song_id}/original.wav"

        log.info("Downloading track from MinIO...")
        input_buffer = io.BytesIO()
        minio_client.download_fileobj(
            MINIO_BUCKET_NAME, source_key, input_buffer)

        # audio separation
        cfg = Config()
        vocal_stream, instr_stream = separate_audio(input_buffer, cfg)

        vocals_key = f"{user_id}/songs/{song_id}/vocals.wav"
        instr_key = f"{user_id}/songs/{song_id}/instrumental.wav"

        log.info("Uploading processed stems back to MinIO...")
        minio_client.upload_fileobj(
            vocal_stream, MINIO_BUCKET_NAME, vocals_key)
        minio_client.upload_fileobj(
            instr_stream, MINIO_BUCKET_NAME, instr_key)

        torch.cuda.empty_cache()
        gc.collect()
        vocal_stream.seek(0)

        # grab lyrics
        segments = transcribe_audio(vocal_stream)

        payload = json.dumps(segments).encode("utf-8")
        json_stream = io.BytesIO(payload)

        json_key = f"{user_id}/songs/{song_id}/lyrics.json"

        minio_client.upload_fileobj(
            json_stream, MINIO_BUCKET_NAME, json_key)

        # grab pitches
        # pitches = extract_pitches(vocal_stream)
        # payload = json.dumps(pitches).encode("utf-8")
        # json_stream = io.BytesIO(payload)

        # json_key = f"{user_id}/songs/{song_id}/pitches.json"
        # minio_client.upload_fileobj(
        #     json_stream, MINIO_BUCKET_NAME, json_key)

        r_client.set(f"task:{song_id}:status", "complete")

        query_filter = {"_id": song_id}
        update_operation = {"$set": {"status": "complete"}}
        m_client.songs.update_one(query_filter, update_operation)

        return True

    except Exception as e:
        log.error("Worker pipeline failed: %s", e, exc_info=True)
        return False
    finally:
        log.info("Cleaning up in-memory data streams...")
        if input_buffer:
            input_buffer.close()
        if vocal_stream and hasattr(vocal_stream, 'close'):
            vocal_stream.close()
        if instr_stream and hasattr(instr_stream, 'close'):
            instr_stream.close()


if __name__ == "__main__":
    kafka_server = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

    log.info(f"Initializing Kafka Queue Client pointing to: {kafka_server}")

    client = KafkaQueueConsumer(
        bootstrap_servers=kafka_server,
        group_id="karaoke-queue"
    )

    client.start_worker(
        topic="song-processing",
        task_handler_callback=process_audio_job
    )
