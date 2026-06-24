import logging
import re

import numpy as np

from app.services.ocr.engine import OCRResult, OCREngine
from app.shared.config import Settings, get_settings
from app.services.preprocessing.deblur import deblur
from app.services.preprocessing.enhance import enhance
from app.services.preprocessing.perspective import correct_perspective

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
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def read(self, image: np.ndarray) -> OCRResult:
        reader = _get_reader(self.settings)

        # 1. Generate multiple image candidates using preprocessing pipelines to maximize OCR accuracy
        candidates = [image]

        try:
            candidates.append(deblur(image))
        except Exception as e:
            logger.debug("Deblur candidate generation failed: %s", e)

        try:
            candidates.append(enhance(image))
        except Exception as e:
            logger.debug("Enhance candidate generation failed: %s", e)

        try:
            candidates.append(correct_perspective(image))
        except Exception as e:
            logger.debug("Perspective candidate generation failed: %s", e)

        # Deduplicate candidates to avoid redundant OCR processing
        unique_candidates = []
        for cand in candidates:
            if cand is not None:
                is_dup = False
                for uc in unique_candidates:
                    if uc.shape == cand.shape and np.array_equal(uc, cand):
                        is_dup = True
                        break
                if not is_dup:
                    unique_candidates.append(cand)

        # 2. Run OCR on all candidates and validate their format
        from app.services.validation.validator import PlateValidator
        validator = PlateValidator(self.settings)

        ocr_candidates = []
        for idx, cand_img in enumerate(unique_candidates):
            try:
                # We use readtext instead of recognize because it isolates the text region first,
                # which is significantly more accurate for crops with borders or background noise.
                results = reader.readtext(
                    cand_img,
                    allowlist=ALLOWLIST,
                    detail=1,
                    paragraph=False,
                )
                if not results:
                    continue

                texts: list[str] = []
                confidences: list[float] = []
                char_confs: list[float] = []

                for _bbox, text, conf in results:
                    cleaned = self._clean_text(text)
                    if cleaned:
                        texts.append(cleaned)
                        confidences.append(float(conf))
                        char_confs.extend([float(conf)] * len(cleaned))

                combined = "".join(texts)
                raw = " ".join(t for _, t, _ in [(None, r[1], r[2]) for r in results])
                avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

                if combined:
                    validation = validator.validate(combined)
                    ocr_candidates.append({
                        "text": combined,
                        "confidence": avg_conf,
                        "char_confidences": char_confs,
                        "raw_output": raw,
                        "is_valid": validation.is_valid
                    })
            except Exception as exc:
                logger.error("OCR candidate %d extraction failed: %s", idx, exc)

        if not ocr_candidates:
            return OCRResult(text="", confidence=0.0, raw_output="")

        # 3. Select the best OCR result
        # Primary: strictly valid format first (matches national plate regex)
        # Secondary: average OCR confidence score
        # Tertiary: longer length to break ties
        ocr_candidates.sort(key=lambda x: (x["is_valid"], x["confidence"], len(x["text"])), reverse=True)
        best = ocr_candidates[0]

        logger.info("OCR Multi-Hypothesis select best: %r (is_valid=%s, conf=%.3f, candidate_count=%d)",
                    best["text"], best["is_valid"], best["confidence"], len(ocr_candidates))

        return OCRResult(
            text=best["text"],
            confidence=best["confidence"],
            char_confidences=best["char_confidences"],
            raw_output=best["raw_output"],
        )

    @staticmethod
    def _clean_text(text: str) -> str:
        cleaned = text.upper()
        cleaned = re.sub(r"[^A-Z0-9]", "", cleaned)
        return cleaned
