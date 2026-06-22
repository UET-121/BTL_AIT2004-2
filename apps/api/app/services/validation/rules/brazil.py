import re

from app.services.validation.rules.base import PlateRule, ValidationResult

MERCOSUL_PATTERN = re.compile(r"^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$")
OLD_PATTERN = re.compile(r"^[A-Z]{3}[0-9]{4}$")

OCR_CORRECTIONS = {
    "O": "0",
    "I": "1",
    "Z": "2",
    "S": "5",
    "B": "8",
}


class BrazilPlateRule(PlateRule):
    """Brazilian Mercosul and old-format plate validation with OCR corrections."""

    def validate(self, text: str) -> ValidationResult:
        normalized = text.upper().strip()
        normalized = re.sub(r"[^A-Z0-9]", "", normalized)

        if MERCOSUL_PATTERN.match(normalized):
            return ValidationResult(
                is_valid=True,
                corrected_text=normalized,
                corrections_applied=[],
                validation_score=1.0,
            )

        if OLD_PATTERN.match(normalized):
            return ValidationResult(
                is_valid=True,
                corrected_text=normalized,
                corrections_applied=[],
                validation_score=1.0,
            )

        corrected, corrections = self._apply_corrections(normalized)
        if MERCOSUL_PATTERN.match(corrected) or OLD_PATTERN.match(corrected):
            return ValidationResult(
                is_valid=True,
                corrected_text=corrected,
                corrections_applied=corrections,
                validation_score=0.8,
            )

        return ValidationResult(
            is_valid=False,
            corrected_text=corrected or normalized,
            corrections_applied=corrections,
            validation_score=0.0,
        )

    def _apply_corrections(self, text: str) -> tuple[str, list[str]]:
        if len(text) < 7:
            return text, []

        chars = list(text)
        corrections: list[str] = []

        for i, char in enumerate(chars):
            if char not in OCR_CORRECTIONS:
                continue
            replacement = OCR_CORRECTIONS[char]
            if len(text) == 7 and i < 3:
                continue
            if len(text) == 7 and i >= 3 and replacement.isalpha():
                continue
            if char != replacement:
                corrections.append(f"{char}->{replacement}@{i}")
                chars[i] = replacement

        return "".join(chars), corrections
