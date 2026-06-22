import time
import json
import pika
import os
import logging
import sys
import queue

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("AI_WORKER")
rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")


class AI_Publisher:
    def __init__(self, exchange="system_event_bus"):
        self.exchange = exchange

    def thread(self, out_queue):
        try:
            parameters = pika.URLParameters(rabbitmq_url)
            parameters.heartbeat = 0
            parameters.blocked_connection_timeout = 300

            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            channel.exchange_declare(exchange=self.exchange, exchange_type="topic")
            logger.info("[RabbitMQ Thread] Đã kết nối và chực chờ gửi dữ liệu!")
        except Exception as e:
            logger.error(f"[RabbitMQ Thread] Lỗi khi kết nối: {e}")
            return
        while True:
            try:
                item = out_queue.get(timeout=1.0)

                if item is None:
                    out_queue.task_done()
                    break

                topic = item.get("topic")
                payload = item.get("payload")

                channel.basic_publish(
                    exchange=self.exchange,
                    routing_key=topic,
                    body=json.dumps(payload),
                )
                out_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Lỗi gửi RabbitMQ ngầm: {e}")

        try:
            connection.close()
            logger.info("[RabbitMQ Thread] Đã đóng kết nối an toàn.")
        except Exception as e:
            logger.warning(f"Lỗi khi đóng connection: {e}")
