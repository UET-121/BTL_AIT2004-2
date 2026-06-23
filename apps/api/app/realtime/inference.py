import logging
import time
import base64
import asyncio
import uuid
import cv2
import numpy as np

from app.realtime.state import shared_state
from app.realtime.broadcaster import broadcaster
from app.realtime.tracker import IoUTracker, Track
from app.realtime.validator import TemporalValidator
from app.realtime.schemas import BBoxSchema, WebSocketEvent
from app.services.factories import get_detector, get_ocr_engine
from app.services.preprocessing.pipeline import PreprocessingPipeline
from app.services.detection.yolo_detector import crop_to_bbox
from app.shared.database import async_session_factory
from app.models.recognition import RecognitionRequest, RecognitionStatus
from app.services.storage import get_storage_service

logger = logging.getLogger(__name__)


def run_async(coro, loop: asyncio.AbstractEventLoop | None) -> None:
    """Helper to safely schedule a coroutine to run on an event loop,
    gracefully handling a closed loop and preventing 'coroutine was never awaited' warnings.
    """
    if loop and not loop.is_closed():
        try:
            asyncio.run_coroutine_threadsafe(coro, loop)
            return
        except RuntimeError as e:
            if "Event loop is closed" in str(e):
                logger.debug("Event loop was closed when attempting to schedule async task.")
            else:
                logger.warning("Failed to schedule async task: %s", e)
    
    # If the loop is not available, is closed, or scheduling failed, close the coroutine
    # object to prevent the 'coroutine was never awaited' warning.
    try:
        coro.close()
    except Exception:
        pass


async def save_confirmed_request(plate_text: str, confidence: float, bbox: any, frame: np.ndarray, vehicle_conf: float = 1.0) -> None:
    """Asynchronously saves a confirmed plate recognition to storage and the PostgreSQL database."""
    try:
        # Convert frame to bytes
        success, buffer = cv2.imencode('.jpg', frame)
        if not success:
            logger.error("Failed to encode frame for database save")
            return
        
        # Save frame to storage service
        storage = get_storage_service()
        filename = f"realtime_{uuid.uuid4()}.jpg"
        image_url = await storage.save(filename, buffer.tobytes())

        # Map bbox to dict format
        bbox_dict = {
            "x": int(bbox.x),
            "y": int(bbox.y),
            "width": int(bbox.width),
            "height": int(bbox.height),
        }

        # Try to extract parent request ID from the source path
        parent_id = None
        source_str = shared_state.source
        if source_str and isinstance(source_str, str):
            try:
                from pathlib import Path
                stem = Path(source_str).stem
                # Check if it is a valid UUID
                uuid.UUID(stem)
                parent_id = stem
            except ValueError:
                pass

        # Create metadata_json
        meta = {"source": "realtime_stream"}
        if parent_id:
            meta["parent_id"] = parent_id

        # Create recognition request record (converting confidence to 0-100 scale for UI)
        record = RecognitionRequest(
            id=uuid.uuid4(),
            image_url=image_url,
            plate_number=plate_text,
            status=RecognitionStatus.COMPLETED,
            confidence_score=float(confidence * 100),
            detection_confidence=float(vehicle_conf * 100),
            ocr_confidence=float(confidence * 100),
            bounding_box=bbox_dict,
            plate_region="BR",
            needs_review=False,
            metadata_json=meta
        )

        async with async_session_factory() as session:
            session.add(record)
            await session.commit()
            logger.info("Saved realtime confirmed plate %s to database.", plate_text)
    except Exception as exc:
        logger.exception("Failed to save confirmed request to database: %s", exc)


def inference_loop_fn(loop: asyncio.AbstractEventLoop | None = None) -> None:
    """Inference loop running in a background thread to process captured frames."""
    logger.info("Starting inference loop thread...")

    detector = get_detector()
    ocr = get_ocr_engine()
    preprocessor = PreprocessingPipeline()
    tracker = IoUTracker()
    temporal_validator = TemporalValidator(min_confirm_count=1)

    last_processed_frame_id = -1
    last_broadcast_time = 0.0
    broadcast_interval = 0.1  # Throttle to max 10 FPS for video websocket transmission

    # FPS tracking variables
    last_frame_time = None
    frame_times = []

    while not shared_state.stop_event.is_set():
        frame, frame_id = shared_state.get_frame()
        if frame is None or frame_id == last_processed_frame_id:
            time.sleep(0.005)  # Wait for new frame
            continue

        last_processed_frame_id = frame_id

        # Resize frame to 1280x720 for faster CPU execution (e.g. if original is 4K)
        h, w = frame.shape[:2]
        if w > 1280 or h > 720:
            scale = 1280 / w
            frame = cv2.resize(frame, (1280, int(h * scale)))

        # Calculate FPS
        now_time = time.perf_counter()
        if last_frame_time is not None:
            elapsed = now_time - last_frame_time
            if elapsed > 0:
                frame_times.append(elapsed)
                if len(frame_times) > 30:
                    frame_times.pop(0)
        last_frame_time = now_time

        fps = 1.0 / (sum(frame_times) / len(frame_times)) if frame_times else 0.0

        # 1. Run detection for both vehicles and plates
        detections = detector.detect_vehicles_and_plates(frame)

        # 2. Update tracker
        tracker.update(detections, frame_id)

        # 3. Process active tracks in the current frame
        timestamp_str = datetime_now_iso()
        
        for track_id, track in tracker.tracks.items():
            if track.last_seen == frame_id and not track.is_confirmed and not getattr(track, "is_rejected", False):
                # Throttle OCR frequency to once every 3 attempts to save CPU
                ocr_attempts = getattr(track, "ocr_attempts", 0)
                track.ocr_attempts = ocr_attempts + 1
                if ocr_attempts % 3 != 0:
                    continue

                # Crop plate region from original frame
                plate_bbox = getattr(track, "plate_bbox", track.bbox)
                crop = crop_to_bbox(frame, plate_bbox)
                
                # Preprocess and run OCR
                preprocessed = preprocessor.run(crop)
                ocr_result = ocr.read(preprocessed.image)

                if ocr_result.text:
                    status, consensus_text, confidence = temporal_validator.add_candidate(
                        track, ocr_result.text, ocr_result.confidence
                    )

                    # Trigger events based on state transitions
                    if status == "confirmed" and not track.is_confirmed:
                        track.is_confirmed = True
                        logger.info("Plate CONFIRMED: %s (Track: %d, Conf: %.2f)", consensus_text, track_id, confidence)
                        
                        # Emit plate.confirmed event
                        event_payload = {
                            "type": "plate.confirmed",
                            "timestamp": timestamp_str,
                            "camera_id": "cam-01",
                            "frame_id": frame_id,
                            "track_id": track_id,
                            "plate_text": consensus_text,
                            "confidence": int(confidence * 100),
                            "vehicle_conf": int(track.vehicle_conf * 100),
                            "plate_conf": int(track.plate_conf * 100),
                            "bbox": {
                                "x": int(plate_bbox.x),
                                "y": int(plate_bbox.y),
                                "width": int(plate_bbox.width),
                                "height": int(plate_bbox.height)
                            }
                        }
                        run_async(broadcaster.broadcast(event_payload), loop)
                        # Save to database
                        run_async(
                            save_confirmed_request(consensus_text, confidence, plate_bbox, frame, track.vehicle_conf),
                            loop
                        )

                    elif status == "rejected" and not getattr(track, "is_rejected", False):
                        track.is_rejected = True
                        logger.info("Plate REJECTED: %s (Track: %d)", consensus_text, track_id)
                        event_payload = {
                            "type": "plate.rejected",
                            "timestamp": timestamp_str,
                            "camera_id": "cam-01",
                            "frame_id": frame_id,
                            "track_id": track_id,
                            "plate_text": consensus_text,
                            "confidence": int(confidence * 100),
                            "vehicle_conf": int(track.vehicle_conf * 100),
                            "plate_conf": int(track.plate_conf * 100),
                            "bbox": {
                                "x": int(plate_bbox.x),
                                "y": int(plate_bbox.y),
                                "width": int(plate_bbox.width),
                                "height": int(plate_bbox.height)
                            }
                        }
                        run_async(broadcaster.broadcast(event_payload), loop)

        # 4. Broadcast live frame + bounding box overlay to active clients
        now = time.perf_counter()
        if now - last_broadcast_time >= broadcast_interval:
            last_broadcast_time = now

            # Only encode image if clients are connected to save CPU cycles
            if broadcaster.active_connections:
                # Resize image slightly if it is too large, to optimize bandwidth
                h, w = frame.shape[:2]
                max_w = 1024
                if w > max_w:
                    scale = max_w / w
                    frame_resized = cv2.resize(frame, (max_w, int(h * scale)))
                else:
                    frame_resized = frame
                    scale = 1.0

                success, buffer = cv2.imencode('.jpg', frame_resized, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if success:
                    image_base64 = base64.b64encode(buffer).decode('utf-8')

                    # Build active detections list mapping coordinates to original scale
                    active_detections = []
                    for t_id, t in tracker.tracks.items():
                        if t.last_seen == frame_id:
                            status_str = "confirmed" if t.is_confirmed else ("rejected" if len(t.candidates) >= temporal_validator.max_candidates else "pending")
                            txt, conf = temporal_validator._get_consensus_text_and_conf(t)
                            
                            p_bbox = getattr(t, "plate_bbox", t.bbox)
                            v_bbox = t.bbox

                            active_detections.append({
                                "track_id": t_id,
                                "vehicle_bbox": {
                                    "x": int((v_bbox.x / w) * 100),
                                    "y": int((v_bbox.y / h) * 100),
                                    "width": int((v_bbox.width / w) * 100),
                                    "height": int((v_bbox.height / h) * 100)
                                },
                                "plate_bbox": {
                                    "x": int((p_bbox.x / w) * 100),
                                    "y": int((p_bbox.y / h) * 100),
                                    "width": int((p_bbox.width / w) * 100),
                                    "height": int((p_bbox.height / h) * 100)
                                },
                                "status": status_str,
                                "text": txt,
                                "vehicle_confidence": int(t.vehicle_conf * 100),
                                "plate_confidence": int(t.plate_conf * 100),
                                "ocr_confidence": int(conf * 100),
                                "confidence": int(conf * 100)
                            })

                    frame_event = {
                        "type": "frame.processed",
                        "timestamp": timestamp_str,
                        "camera_id": "cam-01",
                        "frame_id": frame_id,
                        "image_base64": image_base64,
                        "fps": round(fps, 1),
                        "data": {
                            "detections": active_detections
                        }
                    }
                    run_async(broadcaster.broadcast(frame_event), loop)

    # Loop finished. Let's handle status update for parent video request if applicable.
    parent_id = None
    source_str = shared_state.source
    if source_str and isinstance(source_str, str):
        try:
            from pathlib import Path
            stem = Path(source_str).stem
            uuid.UUID(stem)
            parent_id = stem
        except ValueError:
            pass

    if parent_id:
        final_status = RecognitionStatus.COMPLETED
        err_msg = None
        if shared_state.status == "error":
            final_status = RecognitionStatus.FAILED
            err_msg = shared_state.error_message or "Stream processing error"

        try:
            async def update_parent_status():
                async with async_session_factory() as session:
                    from sqlalchemy import update
                    stmt = (
                        update(RecognitionRequest)
                        .where(RecognitionRequest.id == uuid.UUID(parent_id))
                        .values(status=final_status, error_message=err_msg)
                    )
                    await session.execute(stmt)
                    await session.commit()
                    logger.info("Updated parent video request %s status to %s", parent_id, final_status)
            run_async(update_parent_status(), loop)
        except Exception as exc:
            logger.exception("Failed to update parent video request status: %s", exc)

    # Broadcast stream.stopped event so the frontend knows the stream ended
    event_payload = {
        "type": "stream.stopped",
        "timestamp": datetime_now_iso(),
        "camera_id": "cam-01",
        "data": {
            "source": str(shared_state.source) if shared_state.source is not None else None,
            "status": shared_state.status,
            "error_message": shared_state.error_message
        }
    }
    run_async(broadcaster.broadcast(event_payload), loop)

    logger.info("Inference loop thread stopped.")


def datetime_now_iso() -> str:
    """Helper to return current datetime formatted as ISO 8601 with local timezone offset."""
    # Simple ISO formatting
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat()

