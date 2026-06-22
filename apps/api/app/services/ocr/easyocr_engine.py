import logging
import re

import numpy as np

from app.services.ocr.engine import OCRResult, OCREngine
from app.shared.config import Settings, get_settings

logger = logging.getLogger(__name__)

ALLOWLIST = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_reader_instance = None


def _get_reader(settings: Settings):
    global _reader_instance
    if _reader_instance is None:
        import easyocr
        import torch

        gpu_available = torch.cuda.is_available()
        gpu_flag = settings.ocr_gpu or gpu_available

        _reader_instance = easyocr.Reader(
            ["en"],
            gpu=gpu_flag,
            verbose=False,
        )
        logger.info("EasyOCR reader initialized (gpu=%s, config_setting=%s)", gpu_flag, settings.ocr_gpu)
    return _reader_instance



class EasyOCREngine(OCREngine):
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def read(self, image: np.ndarray) -> OCRResult:
        reader = _get_reader(self.settings)
        results = reader.readtext(
            image,
            allowlist=ALLOWLIST,
            detail=1,
        )

        if not results:
            return OCRResult(text="", confidence=0.0, raw_output="")

        texts: list[str] = []
        confidences: list[float] = []
        char_confs: list[float] = []

        for _bbox, text, conf in results:
            if conf < self.settings.ocr_min_confidence:
                continue
            cleaned = self._clean_text(text)
            if cleaned:
                texts.append(cleaned)
                confidences.append(float(conf))
                char_confs.extend([float(conf)] * len(cleaned))

        combined = "".join(texts)
        raw = " ".join(t for _, t, _ in [(None, r[1], r[2]) for r in results])
        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

        logger.debug("OCR raw=%r cleaned=%r conf=%.3f", raw, combined, avg_conf)
        return OCRResult(
            text=combined,
            confidence=avg_conf,
            char_confidences=char_confs,
            raw_output=raw,
        )

    @staticmethod
    def _clean_text(text: str) -> str:
        cleaned = text.upper()
        cleaned = re.sub(r"[^A-Z0-9]", "", cleaned)
        return cleaned
