import time
import os
from queue_client import KafkaQueueConsumer
import io
import logging
from separate import Config, separate_audio
from bucket_client import container_client, MINIO_BUCKET_NAME
from speech import transcribe_audio

log = logging.getLogger(__name__)


def process_audio_job(task):
    data = task.get("data", {})
    song_id = data.get("song_id")
    user_id = data.get("user_id")

    if not song_id or not user_id:
        log.error("Aborting task: Missing essential metadata.")
        return False

    log.info(f"Working on {song_id} for {user_id}")
    try:
        source_key = f"users/{user_id}/songs/{song_id}/original.wav"

        log.info("Downloading track from MinIO...")
        input_buffer = io.BytesIO()
        container_client.download_fileobj(
            MINIO_BUCKET_NAME, source_key, input_buffer)

        cfg = Config()
        vocal_stream, instr_stream = separate_audio(input_buffer, cfg)

        vocals_key = f"users/{user_id}/songs/{song_id}/vocals.wav"
        instr_key = f"users/{user_id}/songs/{song_id}/instrumental.wav"

        log.info("Uploading processed stems back to MinIO...")
        container_client.upload_fileobj(
            vocal_stream, MINIO_BUCKET_NAME, vocals_key)
        container_client.upload_fileobj(
            instr_stream, MINIO_BUCKET_NAME, instr_key)

        segments = transcribe_audio("output_stems/vocals.wav")
        for segment in segments:
            print(
                f"[{segment['start']:.2f}s -> {segment['end']:.2f}s] {segment['text']}")
            # need to convert this to save to a file

        # add the pitch stuff here

        print(
            f"[WORKER DONE] Successfully finished execution for user {user_id}\n")
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
