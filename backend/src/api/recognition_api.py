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

    # Tạo record trong DB
    request = DetectionRequest(
        image_url=image_url,
        status="PENDING",
    )
    db.add(request)
    await db.commit()
    await db.refresh(request)

    # Gửi task sang ai_worker
    try:
        cmd_pub = CommandPublisher()
        cmd_pub.send_message(
            {
                "action": "PROCESS_VIDEO",
                "request_id": request.id,
                "video_url": image_url,
                "object_name": object_name,
            },
            routing_key="task.recognition.process",
        )
        cmd_pub.close()
    except Exception as e:
        log.warning(f"[Recognition] Không thể gửi task tới worker: {e}")

    return {
        "request_id": str(request.id),
        "status": request.status,
        "created_at": request.created_at.isoformat(),
    }


# ─── Danh sách ────────────────────────────────────────────────────────────────

@router.get("")
async def list_recognition_requests(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Trả về danh sách DetectionRequest phân trang."""
    offset = (page - 1) * page_size

    total_result = await db.execute(select(func.count(DetectionRequest.id)))
    total = total_result.scalar_one()
    total_pages = max(1, (total + page_size - 1) // page_size)

    result = await db.execute(
        select(DetectionRequest).order_by(desc(DetectionRequest.created_at)).offset(offset).limit(page_size)
    )
    items = result.scalars().all()

    return {
        "items": [_serialize(r) for r in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


# ─── Chi tiết ─────────────────────────────────────────────────────────────────

@router.get("/{request_id}")
async def get_recognition_request(
    request_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(DetectionRequest).where(DetectionRequest.id == request_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Không tìm thấy request.")
    return _serialize(req)


# ─── Xóa ──────────────────────────────────────────────────────────────────────

@router.delete("/{request_id}")
async def delete_recognition_request(
    request_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(DetectionRequest).where(DetectionRequest.id == request_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Không tìm thấy request.")

    image_url = req.image_url
    await db.delete(req)
    await db.commit()

    # Xóa file MinIO ở background
    if image_url:
        from urllib.parse import urlparse
        path = urlparse(image_url).path
        prefix = f"/{BUCKET_NAME}/"
        if path.startswith(prefix):
            object_key = path[len(prefix):]
            background_tasks.add_task(delete_images_from_minio, BUCKET_NAME, [object_key])

    return {"status": "success", "message": f"Đã xóa request {request_id}"}


# ─── Nội bộ: ai_worker cập nhật kết quả ──────────────────────────────────────

@router.patch("/{request_id}/result")
async def update_recognition_result(
    request_id: int,
    plate_number: Optional[str] = None,
    status: str = "COMPLETED",
    confidence_score: Optional[int] = None,
    detection_confidence: Optional[int] = None,
    ocr_confidence: Optional[int] = None,
    needs_review: bool = False,
    error_message: Optional[str] = None,
    bounding_box: Optional[dict] = None,
    plate_region: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Endpoint nội bộ để ai_worker cập nhật kết quả OCR vào DB."""
    result = await db.execute(select(DetectionRequest).where(DetectionRequest.id == request_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Không tìm thấy request.")

    req.plate_number = plate_number
    req.status = status
    req.confidence_score = confidence_score
    req.detection_confidence = detection_confidence
    req.ocr_confidence = ocr_confidence
    req.needs_review = needs_review
    req.error_message = error_message
    req.bounding_box = bounding_box
    req.plate_region = plate_region
    await db.commit()
    await db.refresh(req)
    return _serialize(req)


# ─── Serializer ──────────────────────────────────────────────────────────────

def _serialize(r: DetectionRequest) -> dict:
    return {
        "id": str(r.id),
        "image_url": r.image_url,
        "plate_number": r.plate_number,
        "status": r.status,
        "error_message": r.error_message,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        "confidence_score": r.confidence_score,
        "detection_confidence": r.detection_confidence,
        "ocr_confidence": r.ocr_confidence,
        "needs_review": r.needs_review or False,
        "bounding_box": r.bounding_box,
        "plate_region": r.plate_region,
        "camera_id": r.camera_id,
        "gate": r.gate,
        "direction": r.direction,
    }
