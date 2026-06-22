import logging
from pathlib import Path

import cv2
import numpy as np
import torch

from ultralytics import YOLO
from app.services.detection.detector import BoundingBox, PlateDetector
from app.shared.config import Settings, get_settings

logger = logging.getLogger(__name__)

VEHICLE_CLASSES = {"car", "truck", "bus", "motorcycle"}


class YoloPlateDetector(PlateDetector):
    """YOLO-based plate detector with 3-tier fallback chain."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
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

    def _tier1_plate_detection(self, image: np.ndarray) -> list[BoundingBox]:
        assert self._model is not None
        results = self._model(image, verbose=False, device=self.device)
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
        results = self._model(image, verbose=False, device=self.device)
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
