from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np


@dataclass
class BoundingBox:
    x: int
    y: int
    width: int
    height: int
    confidence: float = 1.0
    class_name: str = "plate"

    def clamp_to_image(self, height: int, width: int) -> "BoundingBox":
        x = max(0, min(self.x, width - 1))
        y = max(0, min(self.y, height - 1))
        w = max(1, min(self.width, width - x))
        h = max(1, min(self.height, height - y))
        return BoundingBox(
            x=x,
            y=y,
            width=w,
            height=h,
            confidence=self.confidence,
            class_name=self.class_name,
        )


class PlateDetector(ABC):
    @abstractmethod
    def detect(self, image: np.ndarray) -> list[BoundingBox]:
        """Return detected plate bounding boxes sorted by confidence descending."""
