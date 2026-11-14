import re
from datetime import date
from decimal import Decimal

from src.extract.validate import review_reasons

CENT = Decimal("0.01")

FIELD_ORDER = ["supplier", "invoice_number", "invoice_date", "vat_amount", "total"]
FIELD_LABELS = {
    "supplier": "Supplier",
    "invoice_number": "Invoice number",
    "invoice_date": "Date (YYYY-MM-DD)",
    "vat_amount": "VAT amount (e.g. 1245.50)",
    "total": "Total (e.g. 1245.50)",
}

# Only ASCII digits are accepted, so nothing is converted silently
MONEY_PATTERN = re.compile(r"[0-9]+(\.[0-9]{1,2})?")
DATE_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


def to_text(value) -> str | None:
    if value is None:
        return None
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def parse_corrections(raw: dict[str, str]) -> tuple[dict, list[str]]:
    """Turn what the reviewer typed into typed values. Empty text means 'no value'."""
    fields, errors = {}, []

    for name in FIELD_ORDER:
        text = (raw.get(name) or "").strip()
        label = FIELD_LABELS[name]

        if not text:
            fields[name] = None
        elif name in ("vat_amount", "total"):
            if MONEY_PATTERN.fullmatch(text):
                fields[name] = Decimal(text).quantize(CENT)
            else:
                errors.append(f"{label}: use digits 0-9 and a dot, for example 1245.50")
        elif name == "invoice_date":
            try:
                if not DATE_PATTERN.fullmatch(text):
                    raise ValueError
                fields[name] = date.fromisoformat(text)
            except ValueError:
                errors.append(f"{label}: use a real date such as 2026-09-04")
        else:
            fields[name] = text

    return fields, errors


def build_review_record(language: str, original: dict, corrected: dict) -> dict:
    corrected_text = {name: to_text(corrected[name]) for name in FIELD_ORDER}
    changed = [name for name in FIELD_ORDER if (original.get(name) or None) != corrected_text[name]]

    return {
        "language": language,
        "original": {name: original.get(name) for name in FIELD_ORDER},
        "corrected": corrected_text,
        "changed_fields": changed,
        "remaining_review_reasons": review_reasons(corrected, language),
    }


def describe_reason(reason: str) -> str:
    kind, _, field = reason.partition(":")
    label = FIELD_LABELS.get(field, field).split(" (")[0]

    if kind == "missing":
        return f"{label} was not found."
    if kind == "extractors_disagree":
        return f"The two methods read different values for {label}."
    if kind == "vat_above_total":
        return "VAT is larger than the total."
    if kind == "vat_rate_mismatch":
        return "VAT does not match the expected rate for this total."
    return reason