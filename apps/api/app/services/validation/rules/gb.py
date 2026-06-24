import re
from app.services.validation.rules.base import PlateRule, ValidationResult

GB_PATTERN = re.compile(r"^[A-Z]{2}[0-9]{2}[A-Z]{3}$")

dict_char_to_int = {
    'O': '0',
    'I': '1',
    'J': '3',
    'A': '4',
    'G': '6',
    'S': '5'
}

dict_int_to_char = {
    '0': 'O',
    '1': 'I',
    '3': 'J',
    '4': 'A',
    '6': 'G',
    '5': 'S'
}


class GBPlateRule(PlateRule):
    """UK/GB license plate validation with character correction mapping."""

    def validate(self, text: str) -> ValidationResult:
        normalized = text.upper().strip()
        normalized = re.sub(r"[^A-Z0-9]", "", normalized)

        if GB_PATTERN.match(normalized):
            return ValidationResult(
                is_valid=True,
                corrected_text=normalized,
                corrections_applied=[],
                validation_score=1.0,
            )

        corrected, corrections = self._apply_corrections(normalized)
        if GB_PATTERN.match(corrected):
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
        if len(text) != 7:
            return text, []

        chars = list(text)
        corrections: list[str] = []
        
        # GB format: LLDDLLL (indices 0, 1, 4, 5, 6 are letters, indices 2, 3 are digits)
        is_letter = [True, True, False, False, True, True, True]
        
        for i, char in enumerate(chars):
            if is_letter[i]:
                # Should be a letter
                if char in dict_int_to_char:
                    replacement = dict_int_to_char[char]
                    if char != replacement:
                        corrections.append(f"{char}->{replacement}@{i}")
                        chars[i] = replacement
            else:
                # Should be a digit
                if char in dict_char_to_int:
                    replacement = dict_char_to_int[char]
                    if char != replacement:
                        corrections.append(f"{char}->{replacement}@{i}")
                        chars[i] = replacement
                    
        return "".join(chars), corrections
