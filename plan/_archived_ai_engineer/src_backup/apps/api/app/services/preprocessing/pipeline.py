from dataclasses import dataclass, field
from enum import Enum

import numpy as np

from app.services.preprocessing.deblur import deblur
from app.services.preprocessing.enhance import enhance
from app.services.preprocessing.perspective import correct_perspective
from app.services.preprocessing.quality import assess_quality


class PreprocessingMode(str, Enum):
    DEFAULT = "default"
    AGGRESSIVE = "aggressive"
    PERSPECTIVE = "perspective"


@dataclass
class PreprocessingResult:
    image: np.ndarray
    applied_stages: list[str] = field(default_factory=list)
    quality: dict = field(default_factory=dict)


class PreprocessingPipeline:
    def run(
        self, image: np.ndarray, mode: PreprocessingMode = PreprocessingMode.DEFAULT
    ) -> PreprocessingResult:
        quality = assess_quality(image)
        result = image.copy()
        applied: list[str] = ["quality_assessment"]

        if mode == PreprocessingMode.PERSPECTIVE:
            result = correct_perspective(result)
            applied.append("perspective")
            return PreprocessingResult(
                image=result, applied_stages=applied, quality=quality
            )

        if mode == PreprocessingMode.AGGRESSIVE or quality.get("is_blurry"):
            result = deblur(result)
            applied.append("deblur")

        if mode == PreprocessingMode.AGGRESSIVE or quality.get("is_low_contrast"):
            result = enhance(result)
            applied.append("enhance")

        if mode == PreprocessingMode.DEFAULT and quality.get("blur_score", 0) > 200:
            return PreprocessingResult(
                image=result, applied_stages=applied, quality=quality
            )

        if mode == PreprocessingMode.AGGRESSIVE:
            result = enhance(result)
            if "enhance" not in applied:
                applied.append("enhance")

        return PreprocessingResult(
            image=result, applied_stages=applied, quality=quality
        )
