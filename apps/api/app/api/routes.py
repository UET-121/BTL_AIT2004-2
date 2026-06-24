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
    StorageService,
    get_storage_service,
)
from app.shared.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/recognition", tags=["recognition"])

MAX_FILE_SIZE = 250 * 1024 * 1024  # 250MB for video support
CONTENT_TYPE_MAP = {
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
    summary="Upload video for plate recognition",
    description="Accepts video, stores it, creates a recognition request, and queues real-time stream processing.",
)
async def create_recognition_request(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_storage_service),
) -> RecognitionRequestSubmitResponse:
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="File must be a video")

    if file.content_type not in CONTENT_TYPE_MAP:
        raise HTTPException(
            status_code=400,
            detail="Allowed file types: video/mp4, video/mpeg, video/quicktime, video/x-msvideo, video/x-matroska",
        )

    extension = CONTENT_TYPE_MAP[file.content_type]
    request_id = uuid.uuid4()
    filename = f"{request_id}.{extension}"
    temp_path: str | None = None
    total_bytes = 0

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{extension}") as temp_file:
            temp_path = temp_file.name
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > MAX_FILE_SIZE:
                    raise HTTPException(status_code=400, detail="File exceeds 250MB limit")
                temp_file.write(chunk)

        if temp_path is None:
            raise HTTPException(status_code=400, detail="Failed to persist upload")

        image_url = await storage.save_path(filename, temp_path)

        # For videos, preserve a local copy and launch the real-time stream
        import shutil
        from app.shared.config import get_settings
        from app.realtime.manager import stream_manager

        settings = get_settings()
        upload_dir_path = Path(settings.upload_dir)
        upload_dir_path.mkdir(parents=True, exist_ok=True)
        local_video_path = upload_dir_path / filename
        shutil.copy2(temp_path, local_video_path)

        # Automatically launch real-time stream with this local file
        stream_manager.stop_stream()
        stream_manager.start_stream(str(local_video_path))
        logger.info("Launched real-time stream processing on local video path: %s", local_video_path)
    finally:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)

    # Videos are processed via streaming; mark the request as PENDING initially
    record = RecognitionRequest(
        id=request_id,
        image_url=image_url,
        status=RecognitionStatus.PENDING,
    )
    db.add(record)
    await db.flush()

    logger.info("Created recognition request %s for video streaming", request_id)

    return RecognitionRequestSubmitResponse(
        request_id=record.id,
        status=record.status,
        created_at=record.created_at,
    )


@router.get(
    "/{request_id}",
    response_model=RecognitionRequestResponse,
    summary="Get details of a recognition request",
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


# --- Stream Processing and Real-Time WebSockets ---

from fastapi import WebSocket, WebSocketDisconnect
from app.realtime.manager import stream_manager
from app.realtime.broadcaster import broadcaster
from app.realtime.schemas import StreamStartRequest, StreamStatusResponse

streams_router = APIRouter(prefix="/api/v1/streams", tags=["streams"])
ws_router = APIRouter(tags=["realtime"])


@streams_router.post("/start", response_model=StreamStatusResponse, summary="Start realtime stream")
async def start_realtime_stream(req: StreamStartRequest) -> StreamStatusResponse:
    logger.info("HTTP request to start stream: %s", req.source)
    return stream_manager.start_stream(req.source)


@streams_router.post("/stop", response_model=StreamStatusResponse, summary="Stop realtime stream")
async def stop_realtime_stream() -> StreamStatusResponse:
    logger.info("HTTP request to stop stream")
    return stream_manager.stop_stream()


@streams_router.get("/status", response_model=StreamStatusResponse, summary="Get realtime stream status")
async def get_realtime_stream_status() -> StreamStatusResponse:
    return stream_manager.get_status()


@ws_router.websocket("/ws/live")
async def websocket_live_endpoint(websocket: WebSocket) -> None:
    await broadcaster.connect(websocket)
    try:
        while True:
            # Receive message to keep socket alive and detect disconnections
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        broadcaster.disconnect(websocket)
    except Exception as exc:
        logger.warning("Error in websocket connection: %s", exc)
        broadcaster.disconnect(websocket)
