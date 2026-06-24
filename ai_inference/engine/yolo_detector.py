import logging
from pathlib import Path

import cv2
import numpy as np
import torch

# Monkeypatch torch.load to default weights_only=False for backward compatibility with PyTorch 2.6+ and Ultralytics
_original_torch_load = torch.load
def _patched_torch_load(*args, **kwargs):
    if "weights_only" not in kwargs:
        kwargs["weights_only"] = False
    return _original_torch_load(*args, **kwargs)
torch.load = _patched_torch_load

from ultralytics import YOLO
from engine.detector import BoundingBox, PlateDetector
# Settings mocked from core_pipeline

logger = logging.getLogger(__name__)

VEHICLE_CLASSES = {"car", "truck", "bus", "motorcycle"}


class YoloPlateDetector(PlateDetector):
    """YOLO-based plate detector with 3-tier fallback chain."""

    def __init__(self, settings=None) -> None:
        self.settings = settings
        self._model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info("YOLO plate detector using device: %s", self.device)
        self._load_model()

    def _load_model(self) -> None:
        model_path = self.settings.plate_detection_model
        if not Path(model_path).exists() and not model_path.endswith(".pt"):
            logger.warning("Detection model not found at %s", model_path)
            return
        try:

            self._model = YOLO(model_path)
            logger.info("Loaded YOLO model from %s", model_path)
        except Exception as exc:
            logger.error("Failed to load YOLO model: %s", exc)
            self._model = None

    def _run_yolo_inference(self, model: YOLO, image: np.ndarray, imgsz: int = 640) -> list:
        """Runs YOLO model inference, falling back to CPU if CUDA fails."""
        try:
            return model(image, verbose=False, device=self.device, imgsz=imgsz)
        except Exception as exc:
            if self.device == "cuda":
                logger.warning("YOLO inference failed on CUDA: %s. Falling back to CPU...", exc)
                self.device = "cpu"
                fallback_imgsz = 320 if imgsz == 640 else imgsz
                return model(image, verbose=False, device="cpu", imgsz=fallback_imgsz)
            else:
                logger.error("YOLO inference failed on device %s: %s", self.device, exc)
                raise exc

    def detect(self, image: np.ndarray) -> list[BoundingBox]:
        if not self.settings.use_plate_detection:
            return self._tier3_full_image(image, tier=3)

        boxes: list[BoundingBox] = []
        tier_used = 3

        if self._model is not None:
            boxes = self._tier1_plate_detection(image)
            if boxes:
                tier_used = 1

        if not boxes and self._model is not None:
            boxes = self._tier2_vehicle_detection(image)
            if boxes:
                tier_used = 2

        if not boxes:
            boxes = self._tier3_full_image(image, tier=3)
            tier_used = 3

        for box in boxes:
            box.class_name = f"{box.class_name}:tier{tier_used}"

        return boxes

    def detect_vehicles_and_plates(self, image: np.ndarray) -> list[dict]:
        """
        Detects both vehicles and license plates.
        Returns a list of dicts:
        {
            "vehicle_bbox": BoundingBox,
            "plate_bbox": BoundingBox,
            "vehicle_conf": float,
            "plate_conf": float,
            "class_name": str
        }
        """
        h, w = image.shape[:2]
        vehicles_detected = []
        plates_detected = []

        # 1. Run vehicle detection (always using yolov8n.pt coco model)
        vehicle_model = self._model if self.settings.plate_detection_model == "yolov8n.pt" else getattr(self, "_vehicle_model", None)
        if vehicle_model is None:
            try:
                self._vehicle_model = YOLO("yolov8n.pt")
                vehicle_model = self._vehicle_model
            except Exception as exc:
                logger.error("Failed to load vehicle YOLO model: %s", exc)

        if vehicle_model is not None:
            imgsz = 320 if self.device == "cpu" else 640
            results = self._run_yolo_inference(vehicle_model, image, imgsz=imgsz)
            for result in results:
                if result.boxes is None:
                    continue
                for box in result.boxes:
                    cls_id = int(box.cls[0]) if box.cls is not None else -1
                    class_name = result.names.get(cls_id, "") if hasattr(result, "names") else ""
                    if class_name in VEHICLE_CLASSES:
                        conf = float(box.conf[0])
                        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                        bbox = BoundingBox(
                            x=x1,
                            y=y1,
                            width=x2 - x1,
                            height=y2 - y1,
                            confidence=conf,
                            class_name=class_name
                        ).clamp_to_image(h, w)
                        vehicles_detected.append(bbox)

        is_custom_plate_model = self.settings.plate_detection_model != "yolov8n.pt"
        if is_custom_plate_model and self._model is not None:
            results = self._run_yolo_inference(self._model, image, imgsz=640)
            for result in results:
                if result.boxes is None:
                    continue
                for box in result.boxes:
                    conf = float(box.conf[0])
                    if conf < self.settings.plate_detection_confidence:
                        continue
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    bbox = BoundingBox(
                        x=x1,
                        y=y1,
                        width=x2 - x1,
                        height=y2 - y1,
                        confidence=conf,
                        class_name="plate"
                    ).clamp_to_image(h, w)
                    plates_detected.append(bbox)

        # 3. Associate plates with vehicles, and fallback if needed
        associated_results = []
        used_plates = set()

        for veh in vehicles_detected:
            matching_plate = None
            best_overlap = -1.0
            for i, plt in enumerate(plates_detected):
                x_left = max(veh.x, plt.x)
                y_top = max(veh.y, plt.y)
                x_right = min(veh.x + veh.width, plt.x + plt.width)
                y_bottom = min(veh.y + veh.height, plt.y + plt.height)
                
                if x_right > x_left and y_bottom > y_top:
                    intersection = (x_right - x_left) * (y_bottom - y_top)
                    plate_area = plt.width * plt.height
                    overlap = intersection / plate_area if plate_area > 0 else 0
                    if overlap > 0.5 and overlap > best_overlap:
                        best_overlap = overlap
                        matching_plate = plt
                        used_plates.add(i)

            if matching_plate is None:
                vehicle_h = veh.height
                plate_y1 = veh.y + int(vehicle_h * 0.7)
                plate_y2 = veh.y + vehicle_h
                plate_bbox = BoundingBox(
                    x=veh.x,
                    y=plate_y1,
                    width=veh.width,
                    height=max(1, plate_y2 - plate_y1),
                    confidence=veh.confidence * 0.8,
                    class_name="vehicle_plate_region"
                ).clamp_to_image(h, w)
                plate_conf = veh.confidence * 0.8
            else:
                plate_bbox = matching_plate
                plate_conf = matching_plate.confidence

            associated_results.append({
                "vehicle_bbox": veh,
                "plate_bbox": plate_bbox,
                "vehicle_conf": veh.confidence,
                "plate_conf": plate_conf,
                "class_name": veh.class_name
            })

        for i, plt in enumerate(plates_detected):
            if i not in used_plates:
                veh_bbox = BoundingBox(
                    x=max(0, plt.x - plt.width),
                    y=max(0, plt.y - plt.height * 2),
                    width=plt.width * 3,
                    height=plt.height * 4,
                    confidence=plt.confidence,
                    class_name="car"
                ).clamp_to_image(h, w)
                associated_results.append({
                    "vehicle_bbox": veh_bbox,
                    "plate_bbox": plt,
                    "vehicle_conf": plt.confidence * 0.8,
                    "plate_conf": plt.confidence,
                    "class_name": "car"
                })

        if not associated_results:
            full_box = BoundingBox(
                x=0,
                y=0,
                width=w,
                height=h,
                confidence=0.5,
                class_name="full_image"
            )
            associated_results.append({
                "vehicle_bbox": full_box,
                "plate_bbox": full_box,
                "vehicle_conf": 0.5,
                "plate_conf": 0.5,
                "class_name": "car"
            })

        return associated_results


    def _tier1_plate_detection(self, image: np.ndarray) -> list[BoundingBox]:
        assert self._model is not None
        results = self._run_yolo_inference(self._model, image, imgsz=640)
        boxes: list[BoundingBox] = []
        h, w = image.shape[:2]

        for result in results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                conf = float(box.conf[0])
                if conf < self.settings.plate_detection_confidence:
                    continue
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                cls_id = int(box.cls[0]) if box.cls is not None else -1
                class_name = (
                    result.names.get(cls_id, "plate")
                    if hasattr(result, "names")
                    else "plate"
                )
                bbox = BoundingBox(
                    x=x1,
                    y=y1,
                    width=x2 - x1,
                    height=y2 - y1,
                    confidence=conf,
                    class_name=class_name,
                ).clamp_to_image(h, w)
                boxes.append(bbox)

        boxes.sort(key=lambda b: b.confidence, reverse=True)
        return boxes

    def _tier2_vehicle_detection(self, image: np.ndarray) -> list[BoundingBox]:
        assert self._model is not None
        imgsz = 320 if self.device == "cpu" else 640
        results = self._run_yolo_inference(self._model, image, imgsz=imgsz)
        boxes: list[BoundingBox] = []
        h, w = image.shape[:2]

        for result in results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                cls_id = int(box.cls[0]) if box.cls is not None else -1
                class_name = (
                    result.names.get(cls_id, "") if hasattr(result, "names") else ""
                )
                if class_name not in VEHICLE_CLASSES:
                    continue
                conf = float(box.conf[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                vehicle_h = y2 - y1
                plate_y1 = y1 + int(vehicle_h * 0.7)
                plate_y2 = y2
                bbox = BoundingBox(
                    x=x1,
                    y=plate_y1,
                    width=x2 - x1,
                    height=max(1, plate_y2 - plate_y1),
                    confidence=conf * 0.8,
                    class_name="vehicle_plate_region",
                ).clamp_to_image(h, w)
                boxes.append(bbox)

        boxes.sort(key=lambda b: b.confidence, reverse=True)
        return boxes[:1]

    def _tier3_full_image(self, image: np.ndarray, tier: int = 3) -> list[BoundingBox]:
        h, w = image.shape[:2]
        return [
            BoundingBox(
                x=0,
                y=0,
                width=w,
                height=h,
                confidence=0.5,
                class_name=f"full_image:tier{tier}",
            )
        ]


def crop_to_bbox(image: np.ndarray, bbox: BoundingBox) -> np.ndarray:
    x, y, w, h = bbox.x, bbox.y, bbox.width, bbox.height
    return image[y : y + h, x : x + w].copy()
