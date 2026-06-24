import logging
import threading
import asyncio
from app.realtime.state import shared_state
from app.realtime.capture import capture_thread_fn
from app.realtime.inference import inference_loop_fn
from app.realtime.schemas import StreamStatusResponse

logger = logging.getLogger(__name__)

class StreamManager:
    def __init__(self) -> None:
        self._capture_thread: threading.Thread | None = None
        self._inference_thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def start_stream(self, source: str) -> StreamStatusResponse:
        """Starts the capture and inference threads for the given source."""
        with self._lock:
            if shared_state.is_running:
                logger.info("Stream is already running on source: %s", shared_state.source)
                return self.get_status()

            logger.info("Initiating stream manager with source: %s", source)
            
            # Ensure cleanup of any stale threads
            self._stop_threads_internal()

            # Initialize states
            shared_state.start(source)

            # Get the running asyncio event loop to allow threading callbacks
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None
                logger.warning("Could not detect running asyncio event loop in manager thread. "
                               "WebSockets and DB writes will be disabled.")

            # Spawn capture and inference background threads
            self._capture_thread = threading.Thread(
                target=capture_thread_fn,
                args=(source,),
                name="LPR-CaptureThread",
                daemon=True
            )
            self._inference_thread = threading.Thread(
                target=inference_loop_fn,
                args=(loop,),
                name="LPR-InferenceThread",
                daemon=True
            )

            self._capture_thread.start()
            self._inference_thread.start()

            logger.info("Stream capture and inference threads started.")
            return self.get_status()

    def stop_stream(self) -> StreamStatusResponse:
        """Stops the active capture and inference threads."""
        with self._lock:
            if not shared_state.is_running and shared_state.status != "error":
                logger.info("Stream is already in a stopped state.")
                return self.get_status()

            logger.info("Stopping stream manager threads.")
            shared_state.stop()
            self._stop_threads_internal()
            logger.info("Stream manager threads stopped.")
            return self.get_status()

    def get_status(self) -> StreamStatusResponse:
        """Returns the current status of the stream."""
        return StreamStatusResponse(
            status=shared_state.status,
            source=str(shared_state.source) if shared_state.source is not None else None,
            error_message=shared_state.error_message
        )

    def _stop_threads_internal(self) -> None:
        """Helper to join threads with a timeout to avoid hanging the main application."""
        if self._capture_thread and self._capture_thread.is_alive():
            self._capture_thread.join(timeout=2.0)
        if self._inference_thread and self._inference_thread.is_alive():
            self._inference_thread.join(timeout=2.0)
        
        self._capture_thread = None
        self._inference_thread = None

# Global stream manager instance
stream_manager = StreamManager()
