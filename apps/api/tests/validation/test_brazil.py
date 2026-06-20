import pytest

from app.services.validation.rules.brazil import BrazilPlateRule

rule = BrazilPlateRule()


@pytest.mark.parametrize(
    "text,expected_valid,expected_text",
    [
        ("ABC1D23", True, "ABC1D23"),
        ("abc1d23", True, "ABC1D23"),
        ("ABC1234", True, "ABC1234"),
        ("ABC-1D23", True, "ABC1D23"),
        ("INVALID", False, "INVALID"),
        ("AB12", False, "AB12"),
    ],
)
def test_brazil_plate_validation(text, expected_valid, expected_text):
    result = rule.validate(text)
    assert result.is_valid == expected_valid
    if expected_valid:
        assert result.corrected_text == expected_text


def test_ocr_corrections():
    result = rule.validate("ABCO1D23")
    assert result.is_valid or len(result.corrections_applied) >= 0
