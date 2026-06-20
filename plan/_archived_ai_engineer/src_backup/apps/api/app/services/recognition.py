import logging
import time
from dataclasses import dataclass, field

import cv2
import numpy as np

from app.models.recognition import RecognitionStatus
from app.services.detection.detector import BoundingBox
from app.services.detection.yolo_detector import crop_to_bbox
from app.services.factories import get_detector, get_ocr_engine, get_validator
from app.services.preprocessing.pipeline import PreprocessingMode, PreprocessingPipeline
from app.shared.config import Settings, get_settings

logger = logging.getLogger(__name__)

CONFIDENCE_WEIGHTS = {"detection": 0.2, "ocr": 0.5, "validation": 0.3}


@dataclass
class RecognitionResult:
    plate_text: str | None = None
    confidence_score: float = 0.0
    detection_confidence: float = 0.0
    ocr_confidence: float = 0.0
    needs_review: bool = False
    bounding_box: BoundingBox | None = None
    plate_region: str = "BR"
    error_message: str | None = None
    success: bool = False
    metadata: dict = field(default_factory=dict)


class RecognitionService:
    """Orchestrates detection → preprocessing → OCR → validation → confidence scoring."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.detector = get_detector()
        self.ocr = get_ocr_engine()
        self.validator = get_validator()
        self.preprocessor = PreprocessingPipeline()

    def recognize(self, image_path: str) -> RecognitionResult:
        start = time.perf_counter()
        image = cv2.imread(image_path)
        if image is None:
            return RecognitionResult(
                success=False,
                error_message=f"Could not load image: {image_path}",
                plate_region=self.settings.default_plate_region,
            )

        best_result: RecognitionResult | None = None
        max_attempts = (
            self.settings.max_processing_attempts
            if self.settings.enable_enhanced_retry
            else 1
        )
        modes = [
            PreprocessingMode.DEFAULT,
            PreprocessingMode.AGGRESSIVE,
            PreprocessingMode.PERSPECTIVE,
        ]

        detections = self.detector.detect(image)
        bbox = detections[0] if detections else None
        detection_conf = bbox.confidence if bbox else 0.0
        detection_tier = 3
        if bbox and "tier" in bbox.class_name:
            try:
                detection_tier = int(bbox.class_name.split("tier")[-1])
            except ValueError:
                pass

        crop = crop_to_bbox(image, bbox) if bbox else image

        for attempt in range(max_attempts):
            mode = modes[min(attempt, len(modes) - 1)]
            preprocessed = self.preprocessor.run(crop, mode=mode)
            ocr_result = self.ocr.read(preprocessed.image)
            validation = self.validator.validate(ocr_result.text)

            confidence = self._compute_confidence(
                detection_conf, ocr_result.confidence, validation.validation_score
            )
            needs_review = confidence < self.settings.needs_review_threshold

            attempt_result = RecognitionResult(
                plate_text=(
                    validation.corrected_text if validation.corrected_text else None
                ),
                confidence_score=confidence,
                detection_confidence=detection_conf,
                ocr_confidence=ocr_result.confidence,
                needs_review=needs_review,
                bounding_box=bbox,
                plate_region=self.settings.default_plate_region,
                success=validation.is_valid,
                metadata={
                    "attempts": attempt + 1,
                    "preprocessing_applied": preprocessed.applied_stages,
                    "raw_ocr_text": ocr_result.raw_output or ocr_result.text,
                    "validation_corrections": validation.corrections_applied,
                    "detection_tier": detection_tier,
                    "processing_time_ms": int((time.perf_counter() - start) * 1000),
                },
            )

            if best_result is None or (attempt_result.confidence_score or 0) > (
                best_result.confidence_score or 0
            ):
                best_result = attempt_result

            if (
                validation.is_valid
                and confidence >= self.settings.auto_accept_threshold
            ):
                best_result = attempt_result
                break

            if validation.is_valid and not self.settings.enable_enhanced_retry:
                break

        assert best_result is not None
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        best_result.metadata["processing_time_ms"] = elapsed_ms
        logger.info(
            "Recognition completed in %dms: plate=%s conf=%.3f valid=%s",
            elapsed_ms,
            best_result.plate_text,
            best_result.confidence_score,
            best_result.success,
        )

        if not best_result.success:
            best_result.error_message = (
                f"No valid plate found after {max_attempts} attempt(s). "
                f"Last OCR: {best_result.metadata.get('raw_ocr_text', '')}"
            )

        return best_result

    @staticmethod
    def _compute_confidence(
        detection_conf: float, ocr_conf: float, validation_score: float
    ) -> float:
        return (
            CONFIDENCE_WEIGHTS["detection"] * detection_conf
            + CONFIDENCE_WEIGHTS["ocr"] * ocr_conf
            + CONFIDENCE_WEIGHTS["validation"] * validation_score
        )


def map_result_to_status(
    result: RecognitionResult, settings: Settings
) -> RecognitionStatus:
    if not result.success or not result.plate_text:
        return RecognitionStatus.FAILED

    if result.confidence_score >= settings.auto_accept_threshold:
        return RecognitionStatus.COMPLETED

    if result.confidence_score < settings.needs_review_threshold or result.needs_review:
        return RecognitionStatus.NEEDS_REVIEW

    return RecognitionStatus.COMPLETED
