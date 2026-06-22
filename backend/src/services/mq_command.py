import pika
import json
import time

from pika.exceptions import AMQPError

from shared.config.config import Config
from shared.config.logger import log

RABBITMQ_URL = Config.RABBITMQ_URL


class CommandPublisher:
    def __init__(self):
        self.connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
        self.channel = self.connection.channel()

        self.channel.exchange_declare(
            exchange="system_event_bus", exchange_type="topic"
        )

    def send_message(self, message, routing_key):
        try:
            self.channel.basic_publish(
                exchange="system_event_bus",
                routing_key=routing_key,
                body=json.dumps(message),
                properties=pika.BasicProperties(delivery_mode=2),
            )
            return {
                "status": "success",
                "message": "Đã gửi lệnh thành công vào hàng đợi.",
            }

        except AMQPError as e:
            log.info(f"[!] Lỗi kết nối RabbitMQ: {e}")
            return {
                "status": "error",
                "message": "Không thể kết nối đến hệ thống xử lý ngầm.",
            }
        except Exception as e:
            return {"status": "error", "message": f"Lỗi hệ thống không xác định: {e}"}

    def send_reload_cache_signal(self):
        message = {"command": "RELOAD_CACHE", "timestamp": time.time()}
        res = self.send_message(message, "task.reload.cache")
        return res

    def send_camera_command(self, action: str, camera_id: str, link: str = None):
        message = {
            "action": f"CAMERA_{action.upper()}",
            "camera_id": camera_id,
            "link": link,
            "timestamp": time.time(),
        }
        self.send_message(message, "task.camera.control")

    def send_reg_config(self, thres):
        message = {
            "action": "UPDATE_REG_THRES",
            "license_plate_match_threshold": thres,
        }
        res = self.send_message(message, "task.config.thres")
        return res

    def send_export_command(
        self,
        camera_id=None,
        user_id=None,
        start_time=None,
        end_time=None,
        requested_by=None,
    ):
        message = {
            "action": "EXPORT_DETECTION_LOGS",
            "payload": {
                "camera_id": camera_id,
                "user_id": user_id,
                "start_date": start_time.isoformat() if start_time else None,
                "end_date": end_time.isoformat() if end_time else None,
                "requested_by": requested_by,
            },
            "timestamp": time.time(),
        }
        self.send_message(message, "task.export.detection_logs")

    def send_recognition_export_command(
        self,
        camera_id=None,
        profile_id=None,
        start_time=None,
        end_time=None,
        requested_by=None,
    ):
        message = {
            "action": "EXPORT_RECOGNITION_LOGS",
            "payload": {
                "camera_id": camera_id,
                "profile_id": profile_id,
                "start_date": start_time.isoformat() if start_time else None,
                "end_date": end_time.isoformat() if end_time else None,
                "requested_by": requested_by,
            },
            "timestamp": time.time(),
        }
        self.send_message(message, "task.export.recognition_logs")

    # TODO: Nếu cần thêm các command từ backend, add thêm tại đây

    def close(self):
        if self.connection and self.connection.is_open:
            self.connection.close()
