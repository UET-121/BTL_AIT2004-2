import threading
import cv2
import os
import sys
import logging
import time

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
    "rtsp_transport;tcp"
    "|fflags;nobuffer"
    "|flags;low_delay"
    "|framedrop;1"
    "|stimeout;5000000"
)

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("AI_WORKER")


def connect_with_retry(
    link: str,
    camera_id: str,
    bbox_out_queue,
    is_first_connect: bool,
    max_retry: int = 5,
) -> cv2.VideoCapture | None:
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
        "rtsp_transport;tcp|fflags;nobuffer|flags;low_delay|framedrop;1|stimeout;5000000"
    )

    cap = cv2.VideoCapture(link, cv2.CAP_FFMPEG)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if cap.isOpened():
        return cap

    logger.warning(f"[!] Không thể kết nối RTSP cho camera {camera_id}.")

    if is_first_connect:
        bbox_out_queue.put_nowait(
            {
                "topic": "ui.camera.error",
                "payload": {
                    "camera_id": camera_id,
                    "message": "Sai URL hoặc camera mất nguồn.",
                },
            }
        )
        return None

    for attempt in range(1, max_retry + 1):
        logger.info(
            f"Mất mạng giữa chừng. Đang thử kết nối lại lần {attempt}/{max_retry}..."
        )
        time.sleep(5)

        cap = cv2.VideoCapture(link, cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if cap.isOpened():
            logger.info("Phục hồi kết nối Camera thành công!")
            return cap

    logger.error(f"Đã thử lại {max_retry} lần nhưng Camera {camera_id} vẫn sập.")
    bbox_out_queue.put_nowait(
        {
            "topic": "ui.camera.error",
            "payload": {
                "camera_id": camera_id,
                "message": "Mất kết nối hoàn toàn với Camera.",
            },
        }
    )
    return None


class RTSPStream:
    def __init__(self, url: str, camera_id: str, bbox_out_queue):
        self.url = url
        self.camera_id = camera_id
        self.bbox_out_queue = bbox_out_queue
        self.cap = None
        self.latest_frame = None
        self.lock = threading.Lock()
        self.running = False
        self._thread = None
        self.is_connected = False

    def start(self, is_first_connect: bool = True) -> bool:
        self.cap = connect_with_retry(
            self.url,
            self.camera_id,
            self.bbox_out_queue,
            is_first_connect=is_first_connect,
        )

        if self.cap is None:
            return False

        self.running = True
        self.is_connected = True
        self._thread = threading.Thread(target=self._reader, daemon=True)
        self._thread.start()
        return True

    def _reader(self):
        while self.running:
            ret, frame = self.cap.read()

            if not ret:
                logger.warning(
                    f"[!] Camera {self.camera_id} mất tín hiệu. Reconnecting..."
                )
                self.is_connected = False

                self.bbox_out_queue.put_nowait(
                    {
                        "topic": "ui.camera.disconnected",
                        "payload": {
                            "camera_id": self.camera_id,
                            "message": f"Camera {self.camera_id} mất tín hiệu đột ngột!",
                            "is_active": False,
                        },
                    }
                )

                self.cap = connect_with_retry(
                    self.url,
                    self.camera_id,
                    self.bbox_out_queue,
                    is_first_connect=False,
                )

                if self.cap is None:
                    self.running = False
                    break

                self.is_connected = True
                logger.info(f"[*] Camera {self.camera_id} đã phục hồi kết nối.")
                continue

            with self.lock:
                self.latest_frame = frame

    def read(self):
        with self.lock:
            return self.latest_frame is not None, self.latest_frame

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=5)
        if self.cap:
            self.cap.release()
