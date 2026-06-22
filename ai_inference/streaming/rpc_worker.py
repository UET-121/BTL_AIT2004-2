import aio_pika
import numpy as np
import json
import os
import logging
import asyncio
import sys
import base64
import cv2

from .core_pipeline import LicensePlatePipeline

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("AI_WORKER")

logger.info("Đang nạp AI Model vào RAM/VRAM...")
pipeline = LicensePlatePipeline()
logger.info("Nạp Model thành công. Sẵn sàng xử lý!")


def processing(image_b64):

    img_bytes = base64.b64decode(image_b64)
    np_arr = np.frombuffer(img_bytes, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if image is None:
        raise ValueError("Không thể giải mã ảnh gốc. Ảnh bị hỏng hoặc sai định dạng.")

    detect = pipeline.detect_frame(image)

    if isinstance(detect, list) and len(detect) > 0:
        license_plate_data = detect[0]
    elif isinstance(detect, dict):
        license_plate_data = detect
    else:
        raise ValueError("Không phát hiện biển số nào trong ảnh.")

    bbox = np.array(license_plate_data["box"]).tolist()
    x_min, y_min = max(0, int(bbox[0])), max(0, int(bbox[1]))
    x_max, y_max = max(0, int(bbox[2])), max(0, int(bbox[3]))
    crop_img = image[y_min:y_max, x_min:x_max]
    vector = pipeline.embedding_frame(crop_img).flatten().tolist()

    return vector, bbox


async def get_connection():
    retries = 5
    while retries > 0:
        try:
            return await aio_pika.connect_robust(RABBITMQ_URL, timeout=20)
        except Exception as e:
            logger.warning(f"Waiting for RabbitMQ... ({retries} retries left)")
            await asyncio.sleep(5)
            retries -= 1
    raise Exception("Could not connect to RabbitMQ")


async def rpc_worker_main():
    try:
        connection = await get_connection()
        logger.info("Kết nối Rabbitmq từ rpc_worker thành công")
        channel = await connection.channel()

        await channel.set_qos(prefetch_count=1)

        queue = await channel.declare_queue("rpc_image_tasks", durable=True)
        logger.info("[*] AI Worker đang chờ xử lý ảnh tĩnh (RPC)...")

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    response_data = {}
                    try:
                        payload = json.loads(message.body.decode())
                        image_b64 = payload.get("image_data")

                        logger.info(
                            f"Đã nhận 1 ảnh (Mã vé: {message.correlation_id}). Đang phân tích..."
                        )

                        vector, bbox = await asyncio.to_thread(processing, image_b64)

                        response_data = {
                            "status": "success",
                            "bbox": bbox,
                            "vector": vector,
                        }
                        logger.info("Trích xuất Vector thành công!")

                    except Exception as e:
                        logger.error(f"Lỗi khi xử lý ảnh: {e}")
                        response_data = {
                            "status": "error",
                            "message": f"Lỗi AI Worker: {e}",
                        }

                    try:
                        response_body = json.dumps(response_data).encode()
                    except TypeError as e:
                        logger.error(f"Lỗi Encode JSON: {e}")
                        response_body = json.dumps(
                            {
                                "status": "error",
                                "message": "Lỗi dữ liệu đầu ra không thể JSON",
                            }
                        ).encode()

                    await channel.default_exchange.publish(
                        aio_pika.Message(
                            body=response_body,
                            correlation_id=message.correlation_id,
                        ),
                        routing_key=message.reply_to,
                    )

    except Exception as e:
        logger.error(f"RabbitMQ connection error in RPC loop: {e}")
