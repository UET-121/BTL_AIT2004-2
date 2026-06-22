import logging
import math
import uuid
from pathlib import Path
from uuid import UUID
import tempfile

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recognition import RecognitionRequest, RecognitionStatus
from app.models.schemas import (
    RecognitionRequestListResponse,
    RecognitionRequestResponse,
    RecognitionRequestSubmitResponse,
)
from app.services.storage import (
    ALLOWED_EXTENSIONS,
    StorageService,
    get_storage_service,
    validate_image_magic,
)
from app.shared.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/recognition", tags=["recognition"])

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB for video support
CONTENT_TYPE_MAP = {
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
    "video/mp4": "mp4",
    "video/mpeg": "mpeg",
    "video/quicktime": "mov",
    "video/x-msvideo": "avi",
    "video/x-matroska": "mkv",
}



def _to_response(record: RecognitionRequest) -> RecognitionRequestResponse:
    return RecognitionRequestResponse.model_validate(record)


def _resolve_storage_key(image_url: str) -> str:
    if image_url.startswith("/uploads/"):
        return image_url.removeprefix("/uploads/")
    if image_url.startswith("http://") or image_url.startswith("https://"):
        return Path(image_url).name
    return image_url


@router.post(
    "",
    response_model=RecognitionRequestSubmitResponse,
    summary="Upload media for plate recognition",
    description="Accepts JPEG/PNG image or video, stores it, creates a recognition request, and queues async processing.",
)
async def create_recognition_request(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_storage_service),
) -> RecognitionRequestSubmitResponse:
    if not file.content_type or (not file.content_type.startswith("image/") and not file.content_type.startswith("video/")):
        raise HTTPException(status_code=400, detail="File must be an image or video")

    if file.content_type not in CONTENT_TYPE_MAP:
        raise HTTPException(
            status_code=400,
            detail="Allowed file types: image/jpeg, image/png, video/mp4, video/mpeg, video/quicktime, video/x-msvideo, video/x-matroska",
        )

    extension = CONTENT_TYPE_MAP[file.content_type]
    request_id = uuid.uuid4()
    filename = f"{request_id}.{extension}"
    temp_path: str | None = None
    total_bytes = 0
    prefix = bytearray()

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{extension}") as temp_file:
            temp_path = temp_file.name
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > MAX_FILE_SIZE:
                    raise HTTPException(status_code=400, detail="File exceeds 50MB limit")
                if len(prefix) < 16:
                    prefix.extend(chunk[: 16 - len(prefix)])
                temp_file.write(chunk)

        if file.content_type.startswith("image/"):
            if not validate_image_magic(bytes(prefix), extension):
                raise HTTPException(status_code=400, detail="File content does not match image type")

        if temp_path is None:
            raise HTTPException(status_code=400, detail="Failed to persist upload")

        image_url = await storage.save_path(filename, temp_path)
    finally:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)

    record = RecognitionRequest(
        id=request_id,
        image_url=image_url,
        status=RecognitionStatus.NOT_STARTED,
    )
    db.add(record)
    await db.flush()

    from app.worker.tasks import process_plate_recognition

    process_plate_recognition.delay(str(request_id))

    logger.info("Created recognition request %s", request_id)
    return RecognitionRequestSubmitResponse(
        request_id=record.id,
        status=record.status,
        created_at=record.created_at,
    )


@router.get(
    "/{request_id}",
    response_model=RecognitionRequestResponse,
    summary="Get recognition request by ID",
)
async def get_recognition_request(
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_storage_service),
) -> RecognitionRequestResponse:
    record = await db.get(RecognitionRequest, request_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Recognition request not found")
    res = _to_response(record)
    res.image_url = await storage.get_url(record.image_url)
    return res


@router.get(
    "",
    response_model=RecognitionRequestListResponse,
    summary="List recognition requests",
)
async def list_recognition_requests(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_storage_service),
) -> RecognitionRequestListResponse:
    total_result = await db.execute(select(func.count()).select_from(RecognitionRequest))
    total = total_result.scalar_one()

    offset = (page - 1) * page_size
    result = await db.execute(
        select(RecognitionRequest)
        .order_by(RecognitionRequest.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    items = []
    for r in result.scalars().all():
        res = _to_response(r)
        res.image_url = await storage.get_url(r.image_url)
        items.append(res)
        
    total_pages = math.ceil(total / page_size) if total else 0

    return RecognitionRequestListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post(
    "/{request_id}/reprocess",
    response_model=RecognitionRequestSubmitResponse,
    summary="Reprocess a failed or needs-review request",
)
async def reprocess_recognition_request(
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> RecognitionRequestSubmitResponse:
    record = await db.get(RecognitionRequest, request_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Recognition request not found")

    if record.status not in (RecognitionStatus.FAILED, RecognitionStatus.NEEDS_REVIEW):
        raise HTTPException(
            status_code=400,
            detail="Only FAILED or NEEDS_REVIEW requests can be reprocessed",
        )

    record.plate_number = None
    record.error_message = None
    record.confidence_score = None
    record.detection_confidence = None
    record.ocr_confidence = None
    record.needs_review = False
    record.bounding_box = None
    record.plate_region = None
    record.metadata_json = None
    record.status = RecognitionStatus.NOT_STARTED
    await db.flush()

    from app.worker.tasks import process_plate_recognition

    process_plate_recognition.delay(str(request_id))
    logger.info("Requeued recognition request %s", request_id)

    return RecognitionRequestSubmitResponse(
        request_id=record.id,
        status=record.status,
        created_at=record.created_at,
    )


@router.delete(
    "/{request_id}",
    status_code=204,
    summary="Delete a recognition request",
)
async def delete_recognition_request(
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_storage_service),
) -> Response:
    record = await db.get(RecognitionRequest, request_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Recognition request not found")

    storage_key = _resolve_storage_key(record.image_url)
    try:
        await storage.delete(storage_key)
    except Exception:
        logger.exception("Storage cleanup failed for request %s; deleting DB record anyway", request_id)

    await db.delete(record)
    await db.commit()
    logger.info("Deleted recognition request %s", request_id)
    return Response(status_code=204)
