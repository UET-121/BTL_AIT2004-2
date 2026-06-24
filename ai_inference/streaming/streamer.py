import os
import sys
import cv2
import time
import base64
import redis
import logging
import numpy as np
import queue
import threading
import io
import boto3
from datetime import datetime

from trackers import ByteTrackTracker
import supervision as sv

from .core_pipeline import LicensePlatePipeline
from .ai_publisher import AI_Publisher
from .camera_buffer import RTSPStream

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
redis_sync = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("AI_WORKER")

MINIO_ENDPOINT = os.getenv("MINIO_URL")
ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "license_plate-recognition")

def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        config=boto3.session.Config(
            connect_timeout=5,
            read_timeout=10,
            retries={"max_attempts": 2}
        )
    )

def stream(camera_id, link):
    try:
        s3_client = None
        if MINIO_ENDPOINT:
            s3_client = get_s3_client()
        redis_sync.get(f"stream_pid:{camera_id}")
        bbox_out_queue = queue.Queue(maxsize=100)
        publisher = AI_Publisher()
        pub_thread = threading.Thread(
            target=publisher.thread,
            args=(bbox_out_queue,),
            daemon=True,
        )
        pub_thread.start()

        pipeline = LicensePlatePipeline()
        current_conf = pipeline.conf
        current_iou = pipeline.iou_thres

        try:
            config_data = redis_sync.hgetall("ai_global_config")
            if config_data:
                current_conf = float(config_data.get(b"conf_thres", current_conf))
                current_iou = float(config_data.get(b"iou_thres", current_iou))
                pipeline.update_thres(current_conf, current_iou)
                logger.info(
                    f"[Camera {camera_id}] Đã nạp cấu hình khởi tạo từ Redis -> Conf: {current_conf}, IOU: {current_iou}"
                )
        except Exception as e:
            logger.warning(
                f"[Camera {camera_id}] Không thể lấy cấu hình khởi tạo, dùng mặc định: {e}"
            )

        tracker = ByteTrackTracker(track_activation_threshold=0.5, lost_track_buffer=30)
        published_tracks = {}

        logger.info(f"[*] Đang thử kết nối luồng Camera: {camera_id}...")
        cap = RTSPStream(link, camera_id, bbox_out_queue)
        if not cap.start(is_first_connect=True):
            return

        try:
            bbox_out_queue.put_nowait(
                {
                    "topic": "ui.camera.started",
                    "payload": {
                        "camera_id": camera_id,
                        "message": "Camera đã kết nối thành công",
                    },
                }
            )
            logger.info(
                f"[*] Đã gửi lệnh kích hoạt WebRTC lên UI cho camera {camera_id}"
            )
        except queue.Full:
            logger.warning("Không thể gửi tín hiệu started do queue đầy!")

        frame_count = 0
        frame_height = int(cap.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frame_width = int(cap.cap.get(cv2.CAP_PROP_FRAME_WIDTH))

        while True:
            if not redis_sync.get(f"stream_pid:{camera_id}"):
                logger.info(
                    f"Nhận được tín hiệu dừng từ hệ thống. Đang chủ động thoát luồng..."
                )
                break

            if not cap.running:
                logger.error(f"Camera {camera_id} không thể phục hồi. Thoát.")
                break

            ret, frame = cap.read()

            if not ret or frame is None:
                time.sleep(0.01)
                continue

            frame_count += 1
            if frame_count % 30 == 0:
                redis_sync.setex(f"heartbeat:{camera_id}", 65, "alive")
                try:
                    config_data = redis_sync.hgetall("ai_global_config")
                    if config_data:
                        new_conf = float(config_data.get(b"conf_thres", current_conf))
                        new_iou = float(config_data.get(b"iou_thres", current_iou))
                        if new_conf != current_conf or new_iou != current_iou:
                            pipeline.update_thres(new_conf, new_iou)
                            current_conf = new_conf
                            current_iou = new_iou
                            logger.info(
                                f"[Camera {camera_id}] Đã cập nhật Threshold -> Conf: {new_conf}, IOU: {new_iou}"
                            )
                except Exception as e:
                    logger.warning(f"Lỗi khi đồng bộ cấu hình Redis: {e}")

            # Frame skipping logic (process 1 out of every 3 frames)
            if frame_count % 3 != 0:
                continue

            ui_boxes = []
            detected_license_plates = pipeline.detect_frame(frame)

            if len(detected_license_plates) > 0:
                xyxy_arr = np.array([license_plate["box"] for license_plate in detected_license_plates])
                conf_arr = np.array([license_plate["scores"] for license_plate in detected_license_plates])
                detections = sv.Detections(xyxy=xyxy_arr, confidence=conf_arr)
                tracked_detections = tracker.update(detections)

                for i in range(len(tracked_detections)):
                    track_id = tracked_detections.tracker_id[i]
                    xyxy = tracked_detections.xyxy[i]

                    x_min = max(0, int(xyxy[0]))
                    y_min = max(0, int(xyxy[1]))
                    x_max = min(frame_width, int(xyxy[2]))
                    y_max = min(frame_height, int(xyxy[3]))

                    ui_boxes.append(
                        {
                            "track_id": int(track_id),
                            "bbox": [x_min, y_min, x_max, y_max],
                        }
                    )

                    last_sent = published_tracks.get(track_id, 0)

                    if time.time() - last_sent > 10.0:
                        crop_img = frame[y_min:y_max, x_min:x_max]
                        if crop_img.size > 0:
                            plate_text = pipeline.recognize_plate(crop_img)
                            if not plate_text:
                                continue # Skip if no text recognized

                            crop_img = cv2.resize(crop_img, (150, 150))
                            success, encoded_img = cv2.imencode(".jpg", crop_img)

                            if success:
                                image_url = None
                                if s3_client:
                                    try:
                                        now = datetime.now()
                                        timestamp = int(now.timestamp() * 1000)
                                        object_name = f"logs/temp/{now.year}/{now.month:02d}/{now.day:02d}/cam_{camera_id}/trk_{track_id}_{timestamp}.jpg"
                                        file_obj = io.BytesIO(encoded_img.tobytes())
                                        s3_client.upload_fileobj(
                                            file_obj,
                                            BUCKET_NAME,
                                            object_name,
                                            ExtraArgs={"ContentType": "image/jpeg"},
                                        )
                                        image_url = f"{MINIO_ENDPOINT}/{BUCKET_NAME}/{object_name}"
                                    except Exception as e:
                                        logger.error(f"MinIO upload error: {e}")

                                try:
                                    bbox_out_queue.put_nowait(
                                        {
                                            "topic": f"license_plate.{camera_id}",
                                            "payload": {
                                                "camera_id": camera_id,
                                                "profile_id": "unknown",
                                                "plate_text": plate_text,
                                                "image_url": image_url,
                                                "track_id": int(track_id),
                                            },
                                        }
                                    )
                                except queue.Full:
                                    logger.warning(
                                        "Queue nội bộ bị đầy! Bỏ qua frame để tránh lag camera."
                                    )
                                published_tracks[track_id] = time.time()

            try:
                if camera_id == "stream_0" and frame is not None:
                    # Publish the annotated frame as base64 for the frontend LivePage
                    fps_val = round(1.0 / (time.time() - _last_frame_time + 1e-9), 1) if '_last_frame_time' in locals() else 0
                    display_frame = cv2.resize(frame, (640, 360))
                    # Draw bboxes on frame
                    for box in ui_boxes:
                        bx = box["bbox"]
                        cv2.rectangle(display_frame, (bx[0] * 640 // frame_width, bx[1] * 360 // frame_height),
                                      (bx[2] * 640 // frame_width, bx[3] * 360 // frame_height), (0, 255, 80), 2)
                    _, jpeg = cv2.imencode(".jpg", display_frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
                    img_b64 = base64.b64encode(jpeg.tobytes()).decode("utf-8")

                    # Build detection list for UI
                    ui_detections = []
                    for box in ui_boxes:
                        ui_detections.append({
                            "track_id": box["track_id"],
                            "bbox": {
                                "x": box["bbox"][0],
                                "y": box["bbox"][1],
                                "width": box["bbox"][2] - box["bbox"][0],
                                "height": box["bbox"][3] - box["bbox"][1],
                            },
                            "text": "",
                            "confidence": 0,
                            "status": "pending",
                        })

                    try:
                        bbox_out_queue.put_nowait({
                            "topic": "ui.live.frame",
                            "payload": {
                                "type": "frame.processed",
                                "image_base64": img_b64,
                                "fps": fps_val,
                                "data": {
                                    "detections": ui_detections,
                                    "current_vehicles": len(ui_boxes),
                                    "total_vehicles": frame_count // 3,
                                },
                            },
                        })
                    except queue.Full:
                        pass

                elif len(ui_boxes) > 0:
                    bbox_out_queue.put_nowait(
                        {
                            "topic": f"ui.license_plate.detected.{camera_id}",
                            "payload": {"camera_id": camera_id, "boxes": ui_boxes},
                        }
                    )
            except queue.Full:
                pass

    except Exception as e:
        logger.error(f"[*] Lỗi CRITICAL trong luồng RTSP của camera {camera_id}: {e}")
    finally:
        logger.info(f"[-] Đang dọn dẹp và ngắt trạng thái của camera {camera_id}")
        if "cap" in locals() and cap.running:
            cap.stop()
        if "bbox_out_queue" in locals():
            if camera_id == "stream_0":
                try:
                    bbox_out_queue.put_nowait({
                        "topic": "ui.live.frame",
                        "payload": {
                            "type": "stream.stopped",
                            "data": {"source": link}
                        }
                    })
                except queue.Full:
                    pass
            try:
                bbox_out_queue.put_nowait(None)
            except queue.Full:
                pass
        redis_sync.delete(f"stream_pid:{camera_id}")
        if camera_id == "stream_0":
            redis_sync.hset("stream:status", mapping={"status": "stopped", "error_message": ""})
