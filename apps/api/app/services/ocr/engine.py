from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import numpy as np


@dataclass
class OCRResult:
    text: str
    confidence: float
    char_confidences: list[float] = field(default_factory=list)
    raw_output: str = ""


class OCREngine(ABC):
    @abstractmethod
    def read(self, image: np.ndarray) -> OCRResult:
        """Extract text from plate image."""
