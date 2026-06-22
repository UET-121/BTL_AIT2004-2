import logging
from datetime import datetime, timezone
from uuid import UUID

from app.models.recognition import RecognitionRequest, RecognitionStatus
from app.services.recognition import RecognitionService, map_result_to_status
from app.shared.config import get_settings
from app.worker.celery_app import celery_app
from app.worker.db import get_sync_session

logger = logging.getLogger(__name__)
settings = get_settings()


def _resolve_image_path(image_url: str) -> str:
    if image_url.startswith("/uploads/"):
        return f"{settings.upload_dir}/{image_url.removeprefix('/uploads/')}"
    return image_url


@celery_app.task(
    bind=True,
    name="process_plate_recognition",
    soft_time_limit=300,
    time_limit=360,
    max_retries=3,
    default_retry_delay=60,
)
def process_plate_recognition(self, request_id: str) -> dict:
    logger.info("Processing recognition request %s", request_id)

    with get_sync_session() as session:
        record = session.get(RecognitionRequest, UUID(request_id))
        if record is None:
            logger.error("Request %s not found", request_id)
            return {"error": "not_found"}

        if record.status == RecognitionStatus.COMPLETED:
            logger.info("Request %s already COMPLETED, skipping", request_id)
            return {"status": "skipped"}

        record.status = RecognitionStatus.PENDING
        record.updated_at = datetime.now(timezone.utc)
        session.flush()
        image_url = record.image_url

    import tempfile
    import os

    local_path = None
    temp_path = None

    try:
        try:
            if settings.storage_type == "minio":
                from app.services.storage import get_storage_service
                storage = get_storage_service(settings)
                ext = os.path.splitext(image_url)[1]
                temp_file = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
                temp_path = temp_file.name
                temp_file.close()

                logger.info("Downloading file %s from MinIO to %s", image_url, temp_path)
                storage.download_sync(image_url, temp_path)
                local_path = temp_path
            else:
                local_path = _resolve_image_path(image_url)

            service = RecognitionService()

            ext = os.path.splitext(image_url)[1].lower().lstrip(".")
            is_video = ext in {"mp4", "avi", "mov", "mpeg", "mkv"}

            if is_video:
                logger.info("Processing as video file: %s", local_path)
                result = service.recognize_video(local_path)
            else:
                logger.info("Processing as image file: %s", local_path)
                result = service.recognize(local_path)

            with get_sync_session() as session:
                record = session.get(RecognitionRequest, UUID(request_id))
                if record is None:
                    return {"error": "not_found"}

                final_status = map_result_to_status(result, settings)
                record.plate_number = result.plate_text
                record.confidence_score = result.confidence_score
                record.detection_confidence = result.detection_confidence
                record.ocr_confidence = result.ocr_confidence
                record.needs_review = result.needs_review
                record.bounding_box = (
                    {
                        "x": result.bounding_box.x,
                        "y": result.bounding_box.y,
                        "width": result.bounding_box.width,
                        "height": result.bounding_box.height,
                    }
                    if result.bounding_box
                    else None
                )
                record.plate_region = result.plate_region
                record.metadata_json = result.metadata
                record.status = final_status
                record.error_message = result.error_message
                record.updated_at = datetime.now(timezone.utc)

                logger.info(
                    "Request %s finished: status=%s plate=%s confidence=%.3f",
                    request_id,
                    final_status.value,
                    result.plate_text,
                    result.confidence_score or 0,
                )
                return {"status": final_status.value, "plate_number": result.plate_text}

        except Exception as exc:
            logger.exception("Recognition failed for %s", request_id)
            with get_sync_session() as session:
                record = session.get(RecognitionRequest, UUID(request_id))
                if record:
                    record.status = RecognitionStatus.FAILED
                    record.error_message = str(exc)
                    record.updated_at = datetime.now(timezone.utc)

            if self.request.retries < self.max_retries:
                raise self.retry(exc=exc)
            return {"status": "FAILED", "error": str(exc)}
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
                logger.info("Cleaned up temporary file %s", temp_path)
            except Exception as e:
                logger.warning("Failed to delete temp file %s: %s", temp_path, e)

