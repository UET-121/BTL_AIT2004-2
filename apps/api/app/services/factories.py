import logging
from functools import lru_cache

from app.services.detection.detector import PlateDetector
from app.services.detection.yolo_detector import YoloPlateDetector
from app.services.ocr.engine import OCREngine
from app.services.ocr.easyocr_engine import EasyOCREngine
from app.services.validation.validator import PlateValidator
from app.shared.config import Settings, get_settings

logger = logging.getLogger(__name__)


@lru_cache
def get_detector() -> PlateDetector:
    settings = get_settings()
    if settings.use_onnx_inference:
        try:
            from app.services.detection.onnx_detector import OnnxPlateDetector
            detector = OnnxPlateDetector(settings)
            if detector.is_loaded():
                logger.info("Successfully loaded and initialized ONNX Plate Detector")
                return detector
            else:
                logger.warning("ONNX detector models failed to load. Falling back to PyTorch YOLO.")
        except Exception as exc:
            logger.error("Failed to initialize ONNX detector: %s. Falling back to PyTorch YOLO.", exc)
    return YoloPlateDetector(settings)


@lru_cache
def get_ocr_engine() -> OCREngine:
    return EasyOCREngine(get_settings())


@lru_cache
def get_validator() -> PlateValidator:
    return PlateValidator(get_settings())


def preload_ml_components() -> None:
    """Eager-load ML singletons at worker startup."""
    get_detector()
    get_ocr_engine()
    get_validator()
    logger.info("ML component factories initialized")
