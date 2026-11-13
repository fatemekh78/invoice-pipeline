import re
from decimal import InvalidOperation

from src.extract.parse import parse_date, parse_money
from src.extract.rules import SUPPLIER_PATTERN
from src.generate.formatting import CURRENCY_SYMBOL, SUPPORTED_LANGUAGES


def extract_fields_by_value(text: str, language: str) -> dict:
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unknown language: {language}")

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    supplier = next((line for line in lines if SUPPLIER_PATTERN.match(line)), None)

    symbol = CURRENCY_SYMBOL[language]
    amounts, dates, numbers = [], [], []

    for line in lines:
        if ":" not in line:
            continue
        value = line.split(":", 1)[1].strip()  # ignore the label, keep only the value

        if symbol in value:
            try:
                amounts.append(parse_money(value, language))
            except (ValueError, InvalidOperation):
                pass
            continue

        try:
            dates.append(parse_date(value, language))
            continue
        except ValueError:
            pass

        if re.fullmatch(r"\d{3,}", value):
            numbers.append(value)

    # Exactly one candidate -> use it. Anything else is ambiguous -> None (do not guess).
    two_amounts = len(amounts) == 2
    return {
        "supplier": supplier,
        "invoice_number": numbers[0] if len(numbers) == 1 else None,
        "invoice_date": dates[0] if len(dates) == 1 else None,
        "vat_amount": min(amounts) if two_amounts else None,
        "total": max(amounts) if two_amounts else None,
    }