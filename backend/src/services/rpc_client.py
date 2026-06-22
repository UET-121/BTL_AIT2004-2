import aio_pika
import asyncio
import uuid
import json

from shared.config.config import Config
from shared.config.logger import log

RABBITMQ_URL = Config.RABBITMQ_URL


class ImageProcessorRPC:
    def __init__(self, amqp_url=RABBITMQ_URL):
        self.amqp_url = amqp_url
        self.connection = None
        self.channel = None
        self.callback_queue = None
        self.futures = {}

    async def get_connection(self):
        retries = 5
        while retries > 0:
            try:
                return await aio_pika.connect_robust(RABBITMQ_URL, timeout=20)
            except Exception as e:
                log(f"Waiting for RabbitMQ... ({retries} retries left)")
                await asyncio.sleep(10)
                retries -= 1
        raise Exception("Could not connect to RabbitMQ")

    async def connect(self):
        try:
            self.connection = await self.get_connection()
            self.channel = await self.connection.channel()

            self.callback_queue = await self.channel.declare_queue(exclusive=True)
            await self.callback_queue.consume(self.on_response, no_ack=True)
            log.info("[✓] Đã cấu hình RabbitMQ (RPC Worker)")
        except Exception as e:
            log.error(f"[X] Lỗi khởi tạo: {e}")

    async def on_response(self, message: aio_pika.IncomingMessage):
        future = self.futures.pop(message.correlation_id, None)
        if future:
            future.set_result(json.loads(message.body.decode()))

    async def call_extract_vector(self, image_base64: str) -> dict:
        if not self.connection:
            await self.connect()

        correlation_id = str(uuid.uuid4())
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self.futures[correlation_id] = future
        log.info(f"Đã gửi message với correlation_id:{correlation_id}")
        await self.channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps({"image_data": image_base64}).encode(),
                correlation_id=correlation_id,
                reply_to=self.callback_queue.name,
            ),
            routing_key="rpc_image_tasks",
        )

        return await future


rpc_client = ImageProcessorRPC()
