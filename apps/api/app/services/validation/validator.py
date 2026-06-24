from app.services.validation.rules.base import PlateRule, ValidationResult
from app.services.validation.rules.brazil import BrazilPlateRule
from app.services.validation.rules.gb import GBPlateRule
from app.shared.config import Settings, get_settings


class PlateValidator:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._rules: dict[str, PlateRule] = {
            "BR": BrazilPlateRule(),
            "GB": GBPlateRule(),
        }

    def validate(self, text: str, region: str | None = None) -> ValidationResult:
        if region:
            rule = self._rules.get(region)
            if rule:
                return rule.validate(text)

        default_region = self.settings.default_plate_region
        default_rule = self._rules.get(default_region)
        
        # Try default rule first
        if default_rule:
            res = default_rule.validate(text)
            if res.is_valid:
                return res

        # Try other rules as fallback
        for r_name, r_rule in self._rules.items():
            if r_name == default_region:
                continue
            res = r_rule.validate(text)
            if res.is_valid:
                return res

        # If no rule was valid, return the default rule's result (or a default failure)
        if default_rule:
            return default_rule.validate(text)

        return ValidationResult(
            is_valid=False,
            corrected_text=text,
            corrections_applied=[],
            validation_score=0.0,
        )
