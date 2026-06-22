import asyncio
import aio_pika

from shared.config.config import config
from shared.config.logger import log

RABBITMQ_URL = config.RABBITMQ_URL
RABBITMQ_USER = config.RABBITMQ_DEFAULT_USER
RABBITMQ_PASS = config.RABBITMQ_DEFAULT_PASS

rabbitmq_connection = None
rabbitmq_channel = None
ai_exchange = None


async def get_connection():
    retries = 5
    while retries > 0:
        try:
            return await aio_pika.connect_robust(RABBITMQ_URL, timeout=20)
        except Exception as e:
            print(f"Waiting for RabbitMQ... ({retries} retries left)")
            await asyncio.sleep(10)
            retries -= 1
    raise Exception("Could not connect to RabbitMQ")


async def init_rabbitmq():
    global rabbitmq_connection, rabbitmq_channel, ai_exchange
    try:
        rabbitmq_connection = await get_connection()
        rabbitmq_channel = await rabbitmq_connection.channel()

        ai_exchange = await rabbitmq_channel.declare_exchange(
            name="system_event_bus", type=aio_pika.ExchangeType.TOPIC
        )

        dlx_name = "backend_dlx"
        dlx = await rabbitmq_channel.declare_exchange(
            name=dlx_name, type=aio_pika.ExchangeType.DIRECT
        )

        dlq_name = "backend_failed_tasks"
        dlq = await rabbitmq_channel.declare_queue(name=dlq_name, durable=True)
        await dlq.bind(exchange=dlx, routing_key="failed")

        main_queue = await rabbitmq_channel.declare_queue(
            name="backend_tasks_queue",
            durable=True,
            arguments={
                "x-dead-letter-exchange": dlx_name,
                "x-dead-letter-routing-key": "failed",
            },
        )
        await main_queue.bind(exchange=ai_exchange, routing_key="task.#")

        log.info("[✓] Đã cấu hình RabbitMQ (Backend Publisher)")
    except Exception as e:
        log.error(f"[X] Lỗi khởi tạo RabbitMQ: {e}")


async def close_rabbitmq():
    global rabbitmq_connection
    if rabbitmq_connection and not rabbitmq_connection.is_closed:
        await rabbitmq_connection.close()
        log.info("[-] Đã ngắt kết nối RabbitMQ")
