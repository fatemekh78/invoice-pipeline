import re
from datetime import date
from decimal import Decimal

from src.generate.formatting import MONTHS_EN, SUPPORTED_LANGUAGES


def _check_language(language: str) -> None:
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unknown language: {language}")


def parse_money(text: str, language: str) -> Decimal:
    _check_language(language)

    # Keep only digits, commas and dots (this also drops spaces and the currency symbol)
    cleaned = re.sub(r"[^\d,.]", "", text)

    if language == "en":
        cleaned = cleaned.replace(",", "")   # "1,245.50" -> "1245.50"
    else:
        cleaned = cleaned.replace(",", ".")  # "1245,50" -> "1245.50"

    if not any(character.isdigit() for character in cleaned):
        raise ValueError(f"No amount found in: {text!r}")
    return Decimal(cleaned)


def parse_date(text: str, language: str) -> date:
    _check_language(language)

    if language == "en":
        match = re.search(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", text)
        if match and match.group(2).capitalize() in MONTHS_EN:
            month = MONTHS_EN.index(match.group(2).capitalize()) + 1
            return date(int(match.group(3)), month, int(match.group(1)))
    elif language == "sv":
        match = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
        if match:
            return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    else:
        match = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", text)
        if match:
            return date(int(match.group(3)), int(match.group(2)), int(match.group(1)))

    raise ValueError(f"No date found in: {text!r}")