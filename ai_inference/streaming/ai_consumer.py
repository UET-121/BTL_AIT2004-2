import asyncio
import os
import multiprocessing
import json
import aio_pika
import logging
import sys
import redis.asyncio as aioredis

from .streamer import stream

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
REDIS_URL = os.getenv("REDIS_URL")
redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("AI_WORKER")
ACTIVE_WORKERS = {}


async def process_task(message: aio_pika.IncomingMessage):
    async with message.process():
        payload = json.loads(message.body.decode())
        action = payload.get("action")

        if action == "CAMERA_START":
            camera_id = payload["camera_id"]
            link = payload["link"]
            if camera_id in ACTIVE_WORKERS and ACTIVE_WORKERS[camera_id].is_alive():
                log.warning(f" Camera {camera_id} đã  đang chạy")
                return
            ctx = multiprocessing.get_context("spawn")
            p = ctx.Process(target=stream, args=(camera_id, link))
            p.start()

            ACTIVE_WORKERS[camera_id] = p
            await redis_client.set(f"stream_pid:{camera_id}", p.pid)

        elif action == "CAMERA_STOP":
            camera_id = payload["camera_id"]
            if camera_id in ACTIVE_WORKERS:
                worker_process = ACTIVE_WORKERS[camera_id]
                worker_process.join(timeout=8)

                if worker_process.is_alive():
                    worker_process.terminate()
                    worker_process.join()
                del ACTIVE_WORKERS[camera_id]

            existing_pid = await redis_client.get(f"stream_pid:{camera_id}")
            if existing_pid:
                import signal

                try:
                    os.kill(int(existing_pid), signal.SIGKILL)
                except ProcessLookupError:
                    pass

            await redis_client.delete(f"stream_pid:{camera_id}")
            await redis_client.delete(f"heartbeat:{camera_id}")
            log.info(f"Đã dập tắt luồng camera {camera_id}")


async def start_ai_consumer():
    connection = None
    while connection is None:
        try:
            log.info("Đang cố gắng kết nối tới RabbitMQ...")
            connection = await aio_pika.connect_robust(RABBITMQ_URL)
            log.info("Đã kết nối thành công với RabbitMQ!")
        except Exception as e:
            log.warning(f"RabbitMQ chưa sẵn sàng. Thử lại sau 5 giây... ({e})")
            await asyncio.sleep(5)
    channel = await connection.channel()
    exchange = await channel.declare_exchange(
        "system_event_bus", type=aio_pika.ExchangeType.TOPIC
    )
    queue = await channel.declare_queue("ai_command_queue", durable=True)

    await queue.bind(exchange, routing_key="task.camera.#")

    print("[*] AI Consumer đang lắng nghe các lệnh điều khiển Camera...")

    await queue.consume(process_task)
    await asyncio.Future()
