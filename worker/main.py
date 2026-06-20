import time
import os
from queue_client import KafkaQueueClient


def process_audio_job(task):
    # """Your Core Business Logic Helper Function goes here."""
    # task_type = task.get("task_type")
    # data = task.get("data", {})

    # print(
    #     f"\n[WORKER RUNNING] Starting {task_type} for Song ID: {data.get('song_id')}")

    # # Simulate heavy processing (U-Net audio slicing, etc.)
    # time.sleep(5)

    # print(
    #     f"[WORKER DONE] Successfully separated stems for user {data.get('user_id')}\n")
    # return True  # Signals client to commit offset
    pass


if __name__ == "__main__":
    client = KafkaQueueClient(
        bootstrap_servers=os.environ["KAFKA_BOOTSTRAP_SERVERS"])

    client.listen_queue(
        topic="audio-processing",
        group_id="karaoke-worker-pool",
        task_handler_callback=process_audio_job
    )
