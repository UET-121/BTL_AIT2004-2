import threading
import numpy as np

class StreamState:
    def __init__(self):
        self.lock = threading.Lock()
        self._latest_frame: np.ndarray | None = None
        self._frame_id: int = 0
        self._is_running: bool = False
        self._source: str | int | None = None
        self._status: str = "stopped"  # stopped, starting, running, error
        self._error_message: str | None = None
        
        # Event to signal threads to stop
        self.stop_event = threading.Event()

    def update_frame(self, frame: np.ndarray):
        with self.lock:
            self._latest_frame = frame
            self._frame_id += 1

    def get_frame(self) -> tuple[np.ndarray | None, int]:
        with self.lock:
            return self._latest_frame, self._frame_id

    def start(self, source: str | int):
        with self.lock:
            self._is_running = True
            self._source = source
            self._status = "running"
            self._error_message = None
            self._frame_id = 0
            self._latest_frame = None
            self.stop_event.clear()

    def stop(self):
        with self.lock:
            self._is_running = False
            self._status = "stopped"
            self.stop_event.set()

    def set_error(self, message: str):
        with self.lock:
            self._is_running = False
            self._status = "error"
            self._error_message = message
            self.stop_event.set()

    @property
    def is_running(self) -> bool:
        with self.lock:
            return self._is_running

    @property
    def status(self) -> str:
        with self.lock:
            return self._status

    @property
    def source(self) -> str | int | None:
        with self.lock:
            return self._source

    @property
    def error_message(self) -> str | None:
        with self.lock:
            return self._error_message

# Global singleton for stream state
shared_state = StreamState()
