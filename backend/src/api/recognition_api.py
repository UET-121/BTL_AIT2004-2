"""
/api/v1/recognition  — CRUD cho lịch sử nhận diện từ video upload.

Flow:
1. POST /api/v1/recognition  – upload file video, lưu vào MinIO, tạo DetectionRequest (PENDING),
   gửi task xử lý vào RabbitMQ cho ai_worker.
2. GET  /api/v1/recognition  – danh sách có phân trang.
3. GET  /api/v1/recognition/{id}  – chi tiết một request.
4. DELETE /api/v1/recognition/{id}  – xóa record + file MinIO.

ai_worker sẽ:
- Nhận task qua queue "task.recognition.process"
- Sau khi xử lý xong sẽ gửi AMQP message qua "ui.recognition.done" với
  {request_id, plate_number, status, confidence_score, ...}
- Backend listener (mqlistener.py) nghe "ui.#" và broadcast lên WebSocket,
  đồng thời cập nhật DB thông qua endpoint nội bộ /internal/recognition/update.
"""

import uuid
import io
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, func

from shared.db.database import get_db
from shared.models import DetectionRequest
from shared.core.storage import upload_file_to_minio, delete_images_from_minio
from shared.config.config import Config
from shared.config.logger import log

from ..services.mq_command import CommandPublisher

router = APIRouter(prefix="/api/v1/recognition", tags=["Recognition API"])
BUCKET_NAME = Config.MINIO_BUCKET_NAME


# ─── Upload video ─────────────────────────────────────────────────────────────

@router.post("")
async def create_recognition_request(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload video và tạo DetectionRequest mới."""
    # Kiểm tra định dạng
    allowed_types = {"video/mp4", "video/mpeg", "video/quicktime", "video/x-msvideo", "video/x-matroska"}
    if file.content_type not in allowed_types and not (file.filename or "").lower().endswith(
        (".mp4", ".avi", ".mov", ".mpeg", ".mkv")
    ):
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ file video MP4/AVI/MOV/MKV.")

    # Upload lên MinIO
    ext = (file.filename or "video.mp4").rsplit(".", 1)[-1]
    object_name = f"uploads/videos/{uuid.uuid4()}.{ext}"
    content = await file.read()
    try:
        image_url = upload_file_to_minio(
            io.BytesIO(content),
            object_name,
            extra_args={"ContentType": file.content_type or "video/mp4"},
        )
    except Exception as e:
        log.error(f"[Recognition] Lỗi upload MinIO: {e}")
        raise HTTPException(status_code=500, detail="Không thể lưu file vào storage.")

    return {
        "image_url": image_url,
        "status": "success",
        "message": "Upload thành công"
    }
