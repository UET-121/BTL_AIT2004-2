import aio_pika
import asyncio
import json
from sqlalchemy import update

from shared.config.logger import log
from shared.config.config import Config
from shared.db.database import AsyncSessionLocal
from shared.models.camera import Camera
from shared.models.request import DetectionRequest
from shared.core import redis as redis_module

from .websocket_manager import ws_manager

RABBITMQ_URL = Config.RABBITMQ_URL
STREAM_STATUS_KEY = "stream:status"


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


async def _update_stream_state(status: str, source: str = None, error_message: str = None):
    """Cập nhật Redis stream:status hash."""
    try:
        rc = redis_module.redis_client
        mapping = {"status": status}
        if source is not None:
            mapping["source"] = source
        mapping["error_message"] = error_message or ""
        await rc.hset(STREAM_STATUS_KEY, mapping=mapping)
    except Exception as e:
        log.warning(f"[Listener] Không thể cập nhật Redis stream state: {e}")


async def _update_recognition_result_in_db(request_id: int, payload: dict):
    """Cập nhật kết quả nhận diện vào DetectionRequest."""
    try:
        from sqlalchemy.future import select
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(DetectionRequest).where(DetectionRequest.id == request_id)
            )
            req = result.scalar_one_or_none()
            if req:
                req.plate_number = payload.get("plate_number")
                req.status = payload.get("status", "COMPLETED")
                req.confidence_score = payload.get("confidence_score")
                req.detection_confidence = payload.get("detection_confidence")
                req.ocr_confidence = payload.get("ocr_confidence")
                req.needs_review = payload.get("needs_review", False)
                req.error_message = payload.get("error_message")
                req.bounding_box = payload.get("bounding_box")
                req.plate_region = payload.get("plate_region")
                await db.commit()
                log.info(f"[Listener] Cập nhật DetectionRequest #{request_id}: {req.status}")
    except Exception as e:
        log.error(f"[Listener] Lỗi cập nhật DetectionRequest #{request_id}: {e}")


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
                        # For live frame events, broadcast the inner payload directly
                        # so the frontend receives { type, image_base64, fps, data }
                        if routing_key == "ui.live.frame":
                            await ws_manager.broadcast(payload)
                        else:
                            await ws_manager.broadcast(ui_event)

                        # ── Camera lifecycle events ────────────────────────
                        camera_id_str = payload.get("camera_id")
                        if camera_id_str and str(camera_id_str).isdigit():
                            cam_id = int(camera_id_str)
                            if routing_key == "ui.camera.started":
                                await update_camera_status_in_db(cam_id, True)
                            elif routing_key in [
                                "ui.camera.error",
                                "ui.camera.disconnected",
                            ]:
                                await update_camera_status_in_db(cam_id, False)

                        # ── Single-stream lifecycle events ─────────────────
                        elif routing_key == "ui.stream.started":
                            await _update_stream_state(
                                "running",
                                source=payload.get("source"),
                            )
                        elif routing_key == "ui.stream.stopped":
                            await _update_stream_state("stopped")
                        elif routing_key == "ui.stream.error":
                            await _update_stream_state(
                                "error",
                                error_message=payload.get("message", "Lỗi không xác định"),
                            )

                        # ── Recognition video result callback ──────────────
                        elif routing_key == "ui.recognition.done":
                            request_id = payload.get("request_id")
                            if request_id:
                                await _update_recognition_result_in_db(int(request_id), payload)

                    except Exception as e:
                        log.error(f"Lỗi khi xử lý tin nhắn lên UI: {e}")
    except asyncio.CancelledError:
        log.info("Tiến trình lắng nghe RabbitMQ đã bị hủy.")
    except Exception as e:
        log.error(f"Không thể khởi động UI Listener: {e}")
