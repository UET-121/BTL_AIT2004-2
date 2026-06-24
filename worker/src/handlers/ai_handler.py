import json
import io
import base64
import aio_pika
import asyncio
import numpy as np

from datetime import datetime, timezone
from sqlalchemy import select, text

from shared.db.database import AsyncSessionLocal
from shared.config.logger import log
from shared.config.config import Config
from shared.models import DetectionLog, RecognitionLog, WebhookConfig
from shared.core.redis import redis_client
from shared.core.storage import upload_file_to_minio
from shared.core.webhook_dispatcher import dispatch_webhook_task

from ..task.redis_sync import RAM_PLATE_CACHE

RABBITMQ_URL = Config.RABBITMQ_URL
COOLDOWN_SECONDS = 300

# Threshold doesn't matter much for exact string match but we keep it for API compatibility


async def save_to_database(camera_id: str, profile_id: str, minio_url: str):
    async with AsyncSessionLocal() as db:
        try:
            new_detection = DetectionLog(
                camera_id=int(camera_id),
                image_url=minio_url,
                person_id=str(profile_id) if profile_id is not None else None,
            )
            db.add(new_detection)

            if profile_id is not None:
                redis_key = f"recent_seen:{profile_id}:{camera_id}"
                is_recently_seen = await redis_client.get(redis_key)

                if not is_recently_seen:
                    new_recognition = RecognitionLog(
                        camera_id=int(camera_id),
                        profile_id=profile_id,
                        image_url=minio_url,
                    )
                    db.add(new_recognition)

            await db.commit()

            if profile_id is not None and not is_recently_seen:
                await redis_client.setex(redis_key, COOLDOWN_SECONDS, "1")
                log.info(f"[+] ĐIỂM DANH THÀNH CÔNG: {profile_id} tại {camera_id}")
            elif profile_id is not None:
                log.info(
                    f"[-] Bỏ qua điểm danh cho {profile_id} (Đang trong thời gian cooldown)."
                )

        except Exception as e:
            await db.rollback()
            log.error(f"[DB LỖI] Không thể lưu log vào database: {e}")
            raise e


def upload_base64_to_minio(
    base64_data: str, camera_id: int, log_type: str, track_id: int = 0
) -> str:

    try:
        image_bytes = base64.b64decode(base64_data)

        file_obj = io.BytesIO(image_bytes)

        now = datetime.now()
        timestamp = int(now.timestamp() * 1000)
        object_name = f"logs/{log_type}/{now.year}/{now.month:02d}/{now.day:02d}/cam_{camera_id}/trk_{track_id}_{timestamp}.jpg"

        extra_args = {"ContentType": "image/jpeg"}

        final_url = upload_file_to_minio(file_obj, object_name, extra_args)
        return final_url
    except Exception as e:
        print(f"[Error] Không thể lưu ảnh: {e}")
        return None


async def find_profile_by_plate(plate_text: str) -> int | None:
    if not plate_text:
        return None
        
    plate_text = plate_text.upper().strip()

    if RAM_PLATE_CACHE:
        def search_cache():
            return RAM_PLATE_CACHE.get(plate_text)

        best_match_id = await asyncio.to_thread(search_cache)

        if best_match_id is not None:
            log.debug(f"[CACHE HIT] ID {best_match_id} từ RAM cho biển {plate_text}.")
            return int(best_match_id)

    log.debug(f"[CACHE MISS] Không có trong RAM biển {plate_text}, đang truy vấn Database...")
    async with AsyncSessionLocal() as db:
        query = text("""
            SELECT id, name, license_plate_number
            FROM profiles
            WHERE license_plate_number = :plate_text
            LIMIT 1
        """)

        result = await db.execute(query, {"plate_text": plate_text})
        row = result.fetchone()

        if row:
            profile_id = row.id
            RAM_PLATE_CACHE[plate_text] = profile_id

            log.info(f"[DB HIT] Lấy ID {profile_id} từ DB cho {plate_text} và lưu vào RAM.")
            return profile_id
        else:
            return None


async def process_license_plate_task(message: aio_pika.IncomingMessage, bbox_out_queue):
    async with message.process(requeue=False, ignore_processed=True):
        try:
            data = json.loads(message.body)
            camera_id = data["camera_id"]
            image_url = data.get("image_url")
            track_id = data.get("track_id", 0)
            plate_text = data.get("plate_text")
            log.info(f"[*] Đang xử lý biển số {plate_text} từ {camera_id}...")
            profile_id = None
            log_type = None
            config = None
            if plate_text:
                profile_id = await find_profile_by_plate(plate_text)
                if profile_id:
                    log_type = "recognition"
                    async with AsyncSessionLocal() as db:
                        result = await db.execute(
                            select(WebhookConfig)
                            .where(WebhookConfig.is_active == True)
                            .limit(1)
                        )
                        config = result.scalar_one_or_none()

                        if config and config.url:
                            asyncio.create_task(
                                dispatch_webhook_task(
                                    profile_id=profile_id,
                                    camera_id=camera_id,
                                    detect_time=datetime.now(timezone.utc).isoformat(),
                                    webhook_url=config.url,
                                )
                            )
                else:
                    log_type = "detection"

            if image_url:
                if log_type:
                    prefix = f"{Config.MINIO_ENDPOINT}/{Config.MINIO_BUCKET_NAME}/"
                    if image_url.startswith(prefix):
                        old_object_name = image_url[len(prefix) :]
                        new_object_name = old_object_name.replace(
                            "logs/temp/", f"logs/{log_type}/"
                        )

                        from shared.core.storage import move_object_in_minio

                        success = await asyncio.to_thread(
                            move_object_in_minio, old_object_name, new_object_name
                        )
                        if success:
                            image_url = image_url.replace(
                                "logs/temp/", f"logs/{log_type}/"
                            )

                await save_to_database(camera_id, profile_id, image_url)
                await message.ack()
                log.info(f"[V] Hoàn tất xử lý, ảnh tại: {image_url}")
            else:
                raise Exception("Lỗi: Không nhận được image_url từ AI Worker.")
        except Exception as e:
            log.error(f"Xử lý lỗi: {e}. Đang đẩy vào DLQ...")
            await message.reject(requeue=False)
