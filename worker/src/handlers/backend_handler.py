import asyncio
import json
import aio_pika

from shared.config.logger import log

from ..task.redis_sync import sync_vector_to_redis
from ..task.export import process_export_task
from .ai_handler import update_license_plate_threshold

ACTIVE_EXPORT_WORKERS = []


async def process_backend_task(message: aio_pika.IncomingMessage, bbox_out_queue):
    async with message.process(requeue=False, ignore_processed=True):
        data = json.loads(message.body)
        action = data.get("action")

        log.info(f"[BACKEND] Nhận yêu cầu tác vụ: {action}")
        # TODO Cập nhật các hàm cần thiết (nếu cần) của backend khi request các chức năng phi db vào đây.
        if action == "RELOAD_CACHE":
            await sync_vector_to_redis()
            return

        elif action == "UPDATE_REG_THRES":
            new_license_plate_thresh = data.get("license_plate_match_threshold")
            if new_license_plate_thresh is not None:
                update_license_plate_threshold(float(new_license_plate_thresh))

        elif action == "EXPORT_DETECTION_LOGS":
            asyncio.create_task(
                process_export_task(data.get("payload"), bbox_out_queue, log_type="detection")
            )
        elif action == "EXPORT_RECOGNITION_LOGS":
            asyncio.create_task(
                process_export_task(data.get("payload"), bbox_out_queue, log_type="recognition")
            )
        elif action == "send_alert":
            pass
