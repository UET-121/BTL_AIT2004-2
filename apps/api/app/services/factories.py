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
        logger.info("ONNX inference requested; falling back to YOLO until ONNX detector is wired")
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
