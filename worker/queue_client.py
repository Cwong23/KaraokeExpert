import json
import logging
import signal
import sys
from confluent_kafka import Producer, Consumer, KafkaError

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("KafkaQueue")


class KafkaQueueClient:
    def __init__(self, bootstrap_servers):
        self.bootstrap_servers = bootstrap_servers

    def create_producer(self):
        conf = {
            "bootstrap.servers": self.bootstrap_servers,
            "acks": "all",
            "retries": 5,
            "linger.ms": 10
        }
        return Producer(conf)

    def push_task(self, topic: str, task_type: str, payload: dict):
        producer = self.create_producer()

        message_body = {
            "task_type": task_type,
            "data": payload
        }

        def _delivery_report(err, msg):
            if err is not None:
                logger.error(f"Task delivery failed: {err}")
            else:
                logger.info(
                    f"Task successfully queued to {msg.topic()} [Partition: {msg.partition()}]")

        try:
            serialized_payload = json.dumps(message_body).encode("utf-8")

            producer.produce(topic, value=serialized_payload,
                             callback=_delivery_report)

            producer.flush()

        except Exception as e:
            logger.error(f"Failed to push message to Kafka: {e}")
        finally:
            del producer

    def listen_queue(self, topic: str, group_id: str, task_handler_callback):
        conf = {
            "bootstrap.servers": self.bootstrap_servers,
            "group.id": group_id,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }

        consumer = Consumer(conf)
        consumer.subscribe([topic])
        logger.info(
            f"Worker connected. Listening to topic '{topic}' under consumer group '{group_id}'...")

        def _shutdown_handler(sig, frame):
            logger.info(
                "Shutdown signal received. Closing consumer connection...")
            consumer.close()
            sys.exit(0)

        signal.signal(signal.SIGINT, _shutdown_handler)
        signal.signal(signal.SIGTERM, _shutdown_handler)

        try:
            while True:
                msg = consumer.poll(timeout=1.0)
                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        logger.error(f"Consumer Error: {msg.error()}")
                        break

                try:
                    raw_data = msg.value().decode("utf-8")
                    task = json.loads(raw_data)

                    logger.info(f"Processing task: {task.get('task_type')}")
                    success = task_handler_callback(task)

                    if success:
                        consumer.commit(asynchronous=False)
                        logger.info("Task acknowledged and committed.")
                    else:
                        logger.warning(
                            "Task execution returned false. Skipping commit (will retry depending on configuration).")

                except Exception as eval_err:
                    logger.error(
                        f"Error parsing or handling message payload: {eval_err}")

        except KeyboardInterrupt:
            pass
        finally:
            consumer.close()
