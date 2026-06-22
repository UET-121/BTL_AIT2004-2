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

from ..task.redis_sync import RAM_FACE_CACHE

RABBITMQ_URL = Config.RABBITMQ_URL
COOLDOWN_SECONDS = 300

FACE_MATCH_THRESHOLD = Config.FACE_MATCH_THRESHOLD


def update_license_plate_threshold(new_threshold: float):
    global FACE_MATCH_THRESHOLD
    if 0.0 <= new_threshold <= 1.0:
        FACE_MATCH_THRESHOLD = new_threshold
        log.info(
            f"[Config] Đã cập nhật Ngưỡng nhận diện (LicensePlate Threshold) thành: {new_threshold}"
        )
    else:
        log.warning(
            f"[Config] Giá trị threshold {new_threshold} không hợp lệ (Phải từ 0-1)."
        )


async def save_to_database(camera_id: str, person_id: str, minio_url: str):
    async with AsyncSessionLocal() as db:
        try:
            new_detection = DetectionLog(
                camera_id=int(camera_id),
                image_url=minio_url,
                person_id=str(person_id) if person_id is not None else None,
            )
            db.add(new_detection)

            if person_id is not None:
                redis_key = f"recent_seen:{person_id}:{camera_id}"
                is_recently_seen = await redis_client.get(redis_key)

                if not is_recently_seen:
                    new_recognition = RecognitionLog(
                        camera_id=int(camera_id),
                        profile_id=person_id,
                        image_url=minio_url,
                    )
                    db.add(new_recognition)

            await db.commit()

            if person_id is not None and not is_recently_seen:
                await redis_client.setex(redis_key, COOLDOWN_SECONDS, "1")
                log.info(f"[+] ĐIỂM DANH THÀNH CÔNG: {person_id} tại {camera_id}")
            elif person_id is not None:
                log.info(
                    f"[-] Bỏ qua điểm danh cho {person_id} (Đang trong thời gian cooldown)."
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


async def find_person_by_vector(vector_list: list | str) -> int | None:
    if isinstance(vector_list, str):
        try:
            vector_list = json.loads(vector_list)
        except Exception:
            pass
    target_np = np.array(vector_list, dtype=np.float32)
    target_norm = np.linalg.norm(target_np)

    if RAM_FACE_CACHE:

        def search_cache():
            if target_norm == 0:
                return None, -1.0

            best_id = None
            max_sim = -1.0
            for profile_id, cached_vector in RAM_FACE_CACHE.items():
                cached_norm = np.linalg.norm(cached_vector)
                if cached_norm == 0:
                    continue
                sim = np.dot(target_np, cached_vector) / (target_norm * cached_norm)
                if sim > max_sim:
                    max_sim = sim
                    best_id = profile_id
            return best_id, max_sim

        best_match_id, max_similarity = await asyncio.to_thread(search_cache)

        if max_similarity >= FACE_MATCH_THRESHOLD and best_match_id is not None:
            log.debug(f"[CACHE HIT] ID {best_match_id} từ RAM.")
            return int(best_match_id)

    log.debug("[CACHE MISS] Không có trong RAM, đang truy vấn PGVector...")
    async with AsyncSessionLocal() as db:
        distance_threshold = 1 - FACE_MATCH_THRESHOLD
        query = text("""
            SELECT id, name, license_plate_embedding, license_plate_embedding <=> :vector AS distance
            FROM profiles
            ORDER BY license_plate_embedding <=> :vector
            LIMIT 1
        """)

        vector_str = json.dumps(vector_list)

        result = await db.execute(query, {"vector": vector_str})
        row = result.fetchone()

        if row and row.distance < distance_threshold:
            profile_id = row.id
            vector_data = row.license_plate_embedding
            if isinstance(vector_data, str):
                vector_data = json.loads(vector_data)

            RAM_FACE_CACHE[profile_id] = np.array(vector_data, dtype=np.float32)

            log.info(f"[DB HIT] Lôi ID {profile_id} từ DB lên và đã lưu vào RAM.")
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
            license_plate_vector = data.get("vector")
            log.info(f"[*] Đang xử lý biển số từ {camera_id}...")
            person_id = None
            log_type = None
            config = None
            if license_plate_vector:
                person_id = await find_person_by_vector(license_plate_vector)
                if person_id:
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
                                    profile_id=person_id,
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

                await save_to_database(camera_id, person_id, image_url)
                await message.ack()
                log.info(f"[V] Hoàn tất xử lý, ảnh tại: {image_url}")
            else:
                raise Exception("Lỗi: Không nhận được image_url từ AI Worker.")
        except Exception as e:
            log.error(f"Xử lý lỗi: {e}. Đang đẩy vào DLQ...")
            await message.reject(requeue=False)
