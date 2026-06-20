import json
import logging
import signal
import sys
from confluent_kafka import Consumer, KafkaError

logger = logging.getLogger("KafkaQueue")


class KafkaQueueConsumer:
    def __init__(self, bootstrap_servers: str, group_id: str):
        """Initializes a dedicated Kafka Queue Consumer Client."""
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.consumer = None
        self._shutdown_requested = False

        # Configuration optimal for processing heavy, long-running tasks
        self.config = {
            "bootstrap.servers": self.bootstrap_servers,
            "group.id": self.group_id,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,  # Manual commits only on successful stem separation

            # Max time a worker can spend processing a single audio file before
            # Kafka assumes the container died and reassigns the task (set to 10 mins)
            "max.poll.interval.ms": 600000
        }

    def start_worker(self, topic: str, task_handler_callback):
        """
        Connects to the broker and spins up the infinite task polling worker loop.
        """
        self.consumer = Consumer(self.config)
        self.consumer.subscribe([topic])
        logger.info(
            f"Worker connected. Polling '{topic}' under consumer group '{self.group_id}'...")

        # Setup OS signal traps for graceful teardown
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

        try:
            while not self._shutdown_requested:
                # Poll for a single message from the queue partition
                msg = self.consumer.poll(timeout=1.0)
                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        logger.error(
                            f"Kafka Wire Protocol Error: {msg.error()}")
                        # Do not break here; allow the client to auto-recover/retry connections
                        continue

                # Run payload through business logic execution boundaries
                self._process_message(msg, task_handler_callback)

        finally:
            self._close_connection()

    def _process_message(self, msg, callback):
        """Deserializes message data blocks and calls the target processing script."""
        try:
            raw_data = msg.value().decode("utf-8")
            task = json.loads(raw_data)

            logger.info(f"Processing task event: {task.get('task_type')}")

            # Execute inference logic (convert step)
            success = callback(task)

            if success:
                # Task completed perfectly. Advance the log position offset.
                self.consumer.commit(message=msg, asynchronous=False)
                logger.info("Task acknowledged and committed successfully.")
            else:
                logger.warning(
                    "Core execution returned False. Task offset was NOT committed.")

        except Exception as err:
            logger.error(
                f"Uncaught exception handling payload block: {err}", exc_info=True)

    def _handle_shutdown(self, sig, frame):
        """Intercepts kill signals to allow workers to exit cleanly."""
        logger.info(
            "Shutdown signal caught. Completing current task before close...")
        self._shutdown_requested = True

    def _close_connection(self):
        """Closes sockets and leaves the consumer cluster group cleanly."""
        if self.consumer:
            logger.info("Closing active Kafka cluster connection channels...")
            self.consumer.close()
        sys.exit(0)
