from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ValidationResult:
    is_valid: bool
    corrected_text: str
    corrections_applied: list[str]
    validation_score: float


class PlateRule(ABC):
    @abstractmethod
    def validate(self, text: str) -> ValidationResult:
        pass
