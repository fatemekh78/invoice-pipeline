import re
from decimal import InvalidOperation

from src.extract.parse import parse_date, parse_money

# Words that introduce each field, per language (lowercase)
KEYWORDS = {
    "en": {"invoice_number": ["invoice no"], "invoice_date": ["date"],
           "vat_amount": ["vat"], "total": ["total"]},
    "sv": {"invoice_number": ["fakturanummer"], "invoice_date": ["datum"],
           "vat_amount": ["moms"], "total": ["att betala"]},
    "fi": {"invoice_number": ["laskun numero"], "invoice_date": ["päivämäärä"],
           "vat_amount": ["alv"], "total": ["yhteensä"]},
}

# A supplier line ends with a company suffix, e.g. "Koivu Palvelut Oy"
SUPPLIER_PATTERN = re.compile(r"^.+\s(?:Oy|AB|Ltd)$")


def _value_after_keyword(lines: list[str], keywords: list[str]) -> str | None:
    for line in lines:
        lowered = line.lower()
        for keyword in keywords:
            if lowered.startswith(keyword):
                # "Invoice no.: 10234" -> "10234"
                return line[len(keyword):].lstrip(" .:").strip()
    return None


def _parse_or_none(parser, value: str | None, language: str):
    if value is None:
        return None
    try:
        return parser(value, language)
    except (ValueError, InvalidOperation):
        return None


def extract_fields(text: str, language: str) -> dict:
    if language not in KEYWORDS:
        raise ValueError(f"Unknown language: {language}")
    keywords = KEYWORDS[language]

    # OCR adds blank lines and stray spaces, so clean the lines first
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    supplier = next((line for line in lines if SUPPLIER_PATTERN.match(line)), None)

    number_text = _value_after_keyword(lines, keywords["invoice_number"])
    number_match = re.search(r"\d+", number_text) if number_text else None

    return {
        "supplier": supplier,
        "invoice_number": number_match.group() if number_match else None,
        "invoice_date": _parse_or_none(
            parse_date, _value_after_keyword(lines, keywords["invoice_date"]), language),
        "vat_amount": _parse_or_none(
            parse_money, _value_after_keyword(lines, keywords["vat_amount"]), language),
        "total": _parse_or_none(
            parse_money, _value_after_keyword(lines, keywords["total"]), language),
    }