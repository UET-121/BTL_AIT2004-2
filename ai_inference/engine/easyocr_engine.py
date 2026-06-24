import logging
import re

import numpy as np

from engine.engine import OCRResult, OCREngine
# settings are passed from core_pipeline

logger = logging.getLogger(__name__)

ALLOWLIST = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_reader_instance = None


def _get_reader(settings):
    global _reader_instance
    if _reader_instance is None:
        import easyocr
        import torch

        gpu_available = torch.cuda.is_available()
        gpu_flag = settings.ocr_gpu or gpu_available

        try:
            _reader_instance = easyocr.Reader(
                ["en"],
                gpu=gpu_flag,
                verbose=False,
            )
            logger.info("EasyOCR reader initialized (gpu=%s, config_setting=%s)", gpu_flag, settings.ocr_gpu)
        except Exception as exc:
            if gpu_flag:
                logger.warning("Failed to initialize EasyOCR with GPU: %s. Falling back to CPU...", exc)
                try:
                    _reader_instance = easyocr.Reader(
                        ["en"],
                        gpu=False,
                        verbose=False,
                    )
                    logger.info("EasyOCR reader initialized successfully on CPU")
                except Exception as fallback_exc:
                    logger.error("Failed to initialize EasyOCR even on CPU: %s", fallback_exc)
                    raise fallback_exc
            else:
                logger.error("Failed to initialize EasyOCR: %s", exc)
                raise exc
    return _reader_instance



class EasyOCREngine(OCREngine):
    def __init__(self, settings=None) -> None:
        self.settings = settings

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
