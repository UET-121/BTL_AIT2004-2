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
from app.services.detection.detector import BoundingBox
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


async def save_confirmed_request(plate_text: str, confidence: float, bbox: any, frame_bytes: bytes, vehicle_conf: float = 1.0) -> None:
    """Asynchronously saves a confirmed plate recognition to storage and the PostgreSQL database."""
    try:
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

        logger.info("save_confirmed_request: Starting save for plate_text=%r, parent_id=%s", plate_text, parent_id)
        
        # Save frame to storage service
        storage = get_storage_service()
        filename = f"realtime_{uuid.uuid4()}.jpg"
        image_url = await storage.save(filename, frame_bytes)
        logger.info("save_confirmed_request: Frame uploaded successfully. URL=%s", image_url)

        # Map bbox to dict format
        bbox_dict = {
            "x": int(bbox.x),
            "y": int(bbox.y),
            "width": int(bbox.width),
            "height": int(bbox.height),
        }

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

        logger.info("save_confirmed_request: Adding record to database session...")
        async with async_session_factory() as session:
            session.add(record)
            await session.commit()
            logger.info("Saved realtime confirmed plate %s to database successfully.", plate_text)
    except Exception as exc:
        logger.exception("Failed to save confirmed request to database: %s", exc)


def inference_loop_fn(loop: asyncio.AbstractEventLoop | None = None) -> None:
    """Inference loop running in a background thread to process captured frames."""
    logger.info("Starting inference loop thread...")

    import concurrent.futures
    ocr_pool = concurrent.futures.ThreadPoolExecutor(max_workers=2)

    detector = get_detector()
    ocr = get_ocr_engine()
    preprocessor = PreprocessingPipeline()
    tracker = IoUTracker()
    temporal_validator = TemporalValidator(min_confirm_count=3)

    from app.shared.config import get_settings
    settings = get_settings()
    decimation = max(1, getattr(settings, "detection_decimation", 2))
    target_fps = getattr(settings, "target_fps", 10.0)
    processed_count = 0

    # Unique vehicle tracking state
    track_id_to_vehicle_id = {}
    plate_to_vehicle_id = {}
    next_vehicle_id = 1
    recorded_vehicle_ids = set()

    last_processed_frame_id = -1
    last_broadcast_time = 0.0
    # Sync broadcast throttle with TARGET_FPS so the stream looks smoother
    broadcast_interval = max(0.033, 1.0 / target_fps)

    # FPS tracking variables
    last_frame_time = None
    frame_times = []

    while not shared_state.stop_event.is_set():
        frame, frame_id = shared_state.get_frame()
        if frame is None or frame_id == last_processed_frame_id:
            time.sleep(0.005)  # Wait for new frame
            continue

        last_processed_frame_id = frame_id
        processed_count += 1

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

        # Run detection conditionally based on decimation setting
        run_detection = (processed_count % decimation == 1)

        if run_detection:
            # 1. Run detection on the full frame
            h_orig, w_orig = frame.shape[:2]
            detections = detector.detect_vehicles_and_plates(frame)

            # Optional: We no longer need to shift coordinates because we didn't crop.
            # But we should still clamp them just in case.
            for det in detections:
                v_bbox = det["vehicle_bbox"]
                p_bbox = det["plate_bbox"]

                det["vehicle_bbox"] = BoundingBox(
                    x=v_bbox.x,
                    y=v_bbox.y,
                    width=v_bbox.width,
                    height=v_bbox.height,
                    confidence=v_bbox.confidence,
                    class_name=v_bbox.class_name
                ).clamp_to_image(h_orig, w_orig)

                det["plate_bbox"] = BoundingBox(
                    x=p_bbox.x,
                    y=p_bbox.y,
                    width=p_bbox.width,
                    height=p_bbox.height,
                    confidence=p_bbox.confidence,
                    class_name=p_bbox.class_name
                ).clamp_to_image(h_orig, w_orig)
            
            if detections:
                real_dets = [d for d in detections if getattr(d.get("vehicle_bbox"), "class_name", "") != "full_image"]
                logger.info("Frame %d: detected %d objects (%d real vehicles/plates)", 
                            frame_id, len(detections), len(real_dets))

            # 2. Update tracker with new detections
            tracker.update(detections, frame_id)
        else:
            # Skip detection. Keep all currently active tracks alive at their current positions.
            for track in tracker.tracks.values():
                if track.last_seen == frame_id - 1:
                    track.last_seen = frame_id

        # 3. Process active tracks in the current frame
        timestamp_str = datetime_now_iso()
        
        for track_id, track in tracker.tracks.items():
            # If this is a new track, assign it a temporary/new vehicle ID
            if track_id not in track_id_to_vehicle_id:
                vid = next_vehicle_id
                next_vehicle_id += 1
                track_id_to_vehicle_id[track_id] = vid
                recorded_vehicle_ids.add(vid)

            if track.last_seen == frame_id and not track.is_confirmed and not getattr(track, "is_rejected", False):
                # Throttle OCR frequency to once every 3 attempts to save CPU
                ocr_attempts = getattr(track, "ocr_attempts", 0)
                track.ocr_attempts = ocr_attempts + 1
                
                ocr_future = getattr(track, "ocr_future", None)

                # Submit to ThreadPool if not currently running
                if ocr_future is None:
                    if ocr_attempts % 3 == 1: # Trigger on 1st, 4th, 7th attempt...
                        plate_bbox = getattr(track, "plate_bbox", track.bbox)
                        crop = crop_to_bbox(frame, plate_bbox)
                        preprocessed = preprocessor.run(crop)
                        
                        # We save plate_bbox so the async completion can use the correct coordinates
                        track.ocr_plate_bbox_context = plate_bbox
                        
                        logger.debug("Track %d (attempt %d): Submitting OCR to thread pool...", track_id, track.ocr_attempts)
                        track.ocr_future = ocr_pool.submit(ocr.read, preprocessed.image)
                        
                # Check if an async OCR task has finished
                elif ocr_future.done():
                    try:
                        ocr_result = ocr_future.result()
                        track.ocr_future = None
                        logger.info("Track %d: OCR read text=%r, conf=%.2f", track_id, ocr_result.text, ocr_result.confidence)

                        if ocr_result.text:
                            status, consensus_text, confidence = temporal_validator.add_candidate(
                                track, ocr_result.text, ocr_result.confidence
                            )
                            logger.info("Track %d: TemporalValidator add_candidate -> status=%s, consensus=%r, consensus_conf=%.2f", 
                                        track_id, status, consensus_text, confidence)

                            # Retrieve the plate_bbox context that was used for this OCR run
                            plate_bbox = getattr(track, "ocr_plate_bbox_context", track.bbox)

                            # Trigger events based on state transitions
                            if status == "confirmed" and not track.is_confirmed:
                                track.is_confirmed = True
                                logger.info("Plate CONFIRMED: %s (Track: %d, Conf: %.2f)", consensus_text, track_id, confidence)
                                
                                # Check if plate has already been confirmed in this session
                                if consensus_text in plate_to_vehicle_id:
                                    old_vid = plate_to_vehicle_id[consensus_text]
                                    curr_vid = track_id_to_vehicle_id[track_id]
                                    if curr_vid != old_vid:
                                        track_id_to_vehicle_id[track_id] = old_vid
                                        recorded_vehicle_ids.discard(curr_vid)
                                        logger.info("Merged Track %d (Vehicle ID %d) into existing Vehicle ID %d for plate %s",
                                                    track_id, curr_vid, old_vid, consensus_text)
                                else:
                                    # First time seeing this plate
                                    plate_to_vehicle_id[consensus_text] = track_id_to_vehicle_id[track_id]
                                    
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
                                    logger.info("Track %d: Broadcasting plate.confirmed event and saving to DB...", track_id)
                                    run_async(broadcaster.broadcast(event_payload), loop)
                                    
                                    # Convert frame to bytes synchronously here to prevent blocking asyncio loop
                                    success, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                                    if success:
                                        frame_bytes = buffer.tobytes()
                                        run_async(
                                            save_confirmed_request(consensus_text, confidence, plate_bbox, frame_bytes, track.vehicle_conf),
                                            loop
                                        )
                                    else:
                                        logger.error("Failed to encode frame before saving confirmed request")

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
                    except Exception as e:
                        track.ocr_future = None
                        logger.error("Track %d: Async OCR execution failed: %s", track_id, e)

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
                            "detections": active_detections,
                            "current_vehicles": len(active_detections),
                            "total_vehicles": len(recorded_vehicle_ids)
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

    # Clean up the local video file if it was a streamed upload
    if source_str and isinstance(source_str, str):
        # Allow the capture thread a moment to completely exit and release file handles
        time.sleep(0.5)
        try:
            from pathlib import Path
            video_path = Path(source_str)
            if video_path.is_file():
                # Avoid deleting files outside the upload directory for security
                from app.shared.config import get_settings
                settings = get_settings()
                upload_dir_abs = Path(settings.upload_dir).resolve()
                video_path_abs = video_path.resolve()
                
                # Check if it's inside the upload directory
                if upload_dir_abs in video_path_abs.parents:
                    video_path.unlink(missing_ok=True)
                    logger.info("Cleaned up local video file: %s", video_path)
                else:
                    logger.warning("Prevented deletion of file outside uploads directory: %s", video_path)
        except Exception as clean_exc:
            logger.warning("Failed to clean up local video file %s: %s", source_str, clean_exc)

    logger.info("Inference loop thread stopped.")
    
    # Gracefully shut down OCR thread pool
    ocr_pool.shutdown(wait=False)


def datetime_now_iso() -> str:
    """Helper to return current datetime formatted as ISO 8601 with local timezone offset."""
    # Simple ISO formatting
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat()

