import logging
import time
import cv2
from app.realtime.state import shared_state

logger = logging.getLogger(__name__)

def capture_thread_fn(source: str | int) -> None:
    """Reads frames from the video source in a background thread."""
    actual_source = source
    if isinstance(source, str) and source.isdigit():
        actual_source = int(source)

    logger.info("Starting capture thread with source: %s", source)
    cap = cv2.VideoCapture(actual_source)
    if not cap.isOpened():
        err_msg = f"Failed to open video source: {source}"
        logger.error(err_msg)
        shared_state.set_error(err_msg)
        return

    # Try to get source FPS
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0 or fps > 100:
        fps = 30.0
    frame_delay = 1.0 / fps
    
    # Check if input is a local video file (to pace frame reading)
    is_video_file = False
    if isinstance(actual_source, str):
        # Simplistic check for files vs RTSP/HTTP streams
        is_rtsp = actual_source.startswith("rtsp://") or actual_source.startswith("rtmp://")
        is_http = actual_source.startswith("http://") or actual_source.startswith("https://")
        if not (is_rtsp or is_http):
            is_video_file = True

    logger.info("Video source opened. FPS: %.2f (delay: %.4f), is_video_file: %s", fps, frame_delay, is_video_file)

    consecutive_failures = 0
    max_failures = 15

    while not shared_state.stop_event.is_set():
        start_time = time.perf_counter()
        ret, frame = cap.read()
        if not ret:
            consecutive_failures += 1
            logger.warning("Failed to read frame from source (failure %d/%d)", consecutive_failures, max_failures)
            if consecutive_failures >= max_failures:
                if is_video_file:
                    logger.info("Video file reading complete or reached end.")
                    shared_state.stop()
                    break
                else:
                    logger.info("Attempting to reconnect to stream source...")
                    cap.release()
                    time.sleep(2.0)
                    cap = cv2.VideoCapture(actual_source)
                    if cap.isOpened():
                        logger.info("Reconnection to stream source successful.")
                        consecutive_failures = 0
                    else:
                        err_msg = "Lost stream connection. Reconnection attempts failed."
                        logger.error(err_msg)
                        shared_state.set_error(err_msg)
                        break
            time.sleep(0.5)
            continue
        
        consecutive_failures = 0
        shared_state.update_frame(frame)

        if is_video_file:
            # Limit read speed to simulate real-time playback for video files
            elapsed = time.perf_counter() - start_time
            sleep_time = max(0.001, frame_delay - elapsed)
            time.sleep(sleep_time)
        else:
            # Yield CPU execution slice for RTSP to prevent thread starvation
            time.sleep(0.001)

    cap.release()
    logger.info("Capture thread stopped successfully.")
