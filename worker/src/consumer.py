import asyncio
import json
import multiprocessing
import aio_pika

from shared.config.config import config
from shared.config.logger import log
from .handlers.ai_handler import process_license_plate_task
from .handlers.backend_handler import process_backend_task

RABBITMQ_URL = config.RABBITMQ_URL


async def get_connection():
    retries = 5
    while retries > 0:
        try:
            return await aio_pika.connect_robust(RABBITMQ_URL, timeout=20)
        except Exception as e:
            print(f"Waiting for RabbitMQ... ({retries} retries left)")
            await asyncio.sleep(5)
            retries -= 1
    raise Exception("Could not connect to RabbitMQ")


async def listen_async_queue_and_publish(
    async_queue: asyncio.Queue, exchange: aio_pika.Exchange
):

    log.info("Luồng trung chuyển Async Queue -> RabbitMQ đã kích hoạt.")

    while True:
        try:
            message_data = await async_queue.get()
            if message_data is None:
                continue
            await _publish(exchange, message_data)
        except Exception as e:
            log.error(f"Lỗi async queue listener: {e}")
            await asyncio.sleep(1)


async def _publish(exchange: aio_pika.Exchange, message_data: dict):
    """Shared publish logic"""
    topic = message_data.get("topic")
    data = message_data.get("data")

    if not topic:
        return

    body = json.dumps({"topic": topic, "data": data}).encode("utf-8")
    await exchange.publish(
        aio_pika.Message(
            body=body,
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.NOT_PERSISTENT,
        ),
        routing_key=topic,
    )


from shared.core.redis import redis_client

async def main():
    connection = await get_connection()
    log.info(" [x] Worker đã kết nối thành công tới RabbitMQ")

    await redis_client.init()
    ai_config = await redis_client.hgetall("ai_global_config")
    # if ai_config and "license_plate_match_threshold" in ai_config:
    #     pass


    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=20)  # Tăng lên 20 để tối ưu tốc độ xử lý DB

        event_bus = await channel.declare_exchange(
            "system_event_bus", type=aio_pika.ExchangeType.TOPIC
        )
        async_queue = asyncio.Queue()
        asyncio.create_task(listen_async_queue_and_publish(async_queue, event_bus))

        ai_queue = await channel.declare_queue("ai_detection_queue", durable=True)
        await ai_queue.bind(event_bus, routing_key="license_plate.#")

        dlx_name = "backend_dlx"
        await channel.declare_exchange(dlx_name, type=aio_pika.ExchangeType.DIRECT)
        backend_queue = await channel.declare_queue(
            "backend_tasks_queue",
            durable=True,
            arguments={
                "x-dead-letter-exchange": dlx_name,
                "x-dead-letter-routing-key": "failed",
            },
        )
        await backend_queue.bind(event_bus, routing_key="task.#")

        await ai_queue.consume(lambda msg: process_license_plate_task(msg, async_queue))
        await backend_queue.consume(lambda msg: process_backend_task(msg, async_queue))

        log.info(" [*] Đang chờ tin nhắn từ toàn bộ hệ thống. Bấm CTRL+C để thoát.")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
