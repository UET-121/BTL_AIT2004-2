from app.services.validation.rules.base import PlateRule, ValidationResult
from app.services.validation.rules.brazil import BrazilPlateRule
from app.shared.config import Settings, get_settings


class PlateValidator:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._rules: dict[str, PlateRule] = {
            "BR": BrazilPlateRule(),
        }

    def validate(self, text: str, region: str | None = None) -> ValidationResult:
        region = region or self.settings.default_plate_region
        rule = self._rules.get(region)
        if rule is None:
            return ValidationResult(
                is_valid=False,
                corrected_text=text,
                corrections_applied=[],
                validation_score=0.0,
            )
        return rule.validate(text)
