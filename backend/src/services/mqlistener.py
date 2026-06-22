import aio_pika
import asyncio
import json
from sqlalchemy import update

from shared.config.logger import log
from shared.config.config import Config
from shared.db.database import AsyncSessionLocal
from shared.models.camera import Camera

from .websocket_manager import ws_manager

RABBITMQ_URL = Config.RABBITMQ_URL


async def update_camera_status_in_db(camera_id: int, is_active: bool):
    try:
        async with AsyncSessionLocal() as db:
            stmt = (
                update(Camera).where(Camera.id == camera_id).values(is_active=is_active)
            )
            await db.execute(stmt)
            await db.commit()
            log.info(
                f"Đã đồng bộ DB: Camera {camera_id} -> {'ONLINE' if is_active else 'OFFLINE'}"
            )
    except Exception as e:
        log.error(f"Lỗi cập nhật DB cho Camera {camera_id}: {e}")


async def start_ui_notification_listener():
    try:
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        channel = await connection.channel()

        exchange = await channel.declare_exchange(
            "system_event_bus", type=aio_pika.ExchangeType.TOPIC
        )

        queue = await channel.declare_queue("ui_notifications_queue", durable=True)

        await queue.bind(exchange, routing_key="ui.#")

        log.info("[*] Đã bật Background Listener nhận thông báo UI từ RabbitMQ")

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        payload = json.loads(message.body.decode())
                        routing_key = message.routing_key

                        ui_event = {
                            "topic": routing_key,
                            "data": payload
                        }
                        await ws_manager.broadcast(ui_event)
                        camera_id_str = payload.get("camera_id")

                        if camera_id_str and camera_id_str.isdigit():
                            cam_id = int(camera_id_str)

                            if routing_key == "ui.camera.started":
                                await update_camera_status_in_db(cam_id, True)

                            elif routing_key in [
                                "ui.camera.error",
                                "ui.camera.disconnected",
                            ]:
                                await update_camera_status_in_db(cam_id, False)

                    except Exception as e:
                        log.error(f"Lỗi khi xử lý tin nhắn lên UI: {e}")
    except asyncio.CancelledError:
        log.info("Tiến trình lắng nghe RabbitMQ đã bị hủy.")
    except Exception as e:
        log.error(f"Không thể khởi động UI Listener: {e}")
