from decimal import ROUND_HALF_UP, Decimal

from src.generate.formatting import CENT, SUPPORTED_LANGUAGES

# VAT rates of the synthetic invoices. Real invoices can have several rates,
# so on real data this check would need a list of allowed rates.
EXPECTED_VAT_RATE = {
    "en": Decimal("0.20"),
    "sv": Decimal("0.25"),
    "fi": Decimal("0.255"),
}


def merge_fields(first: dict, second: dict) -> tuple[dict, list[str]]:
    """Combine two extractors. Agree -> value. One is None -> the other's value.
    Both have a value but they differ -> None and a reason (do not guess)."""
    merged, reasons = {}, []
    for name in first:
        a, b = first[name], second[name]
        if a is None:
            merged[name] = b
        elif b is None or a == b:
            merged[name] = a
        else:
            merged[name] = None
            reasons.append(f"extractors_disagree:{name}")
    return merged, reasons


def review_reasons(fields: dict, language: str, tolerance: Decimal = Decimal("0.00")) -> list[str]:
    """Reasons why a human should look at this invoice. Empty list = looks fine."""
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unknown language: {language}")

    reasons = [f"missing:{name}" for name, value in fields.items() if value is None]

    vat, total = fields.get("vat_amount"), fields.get("total")
    if vat is not None and total is not None:
        if vat > total:
            reasons.append("vat_above_total")
        else:
            net = total - vat
            expected_vat = (net * EXPECTED_VAT_RATE[language]).quantize(CENT, rounding=ROUND_HALF_UP)
            if abs(vat - expected_vat) > tolerance:
                reasons.append("vat_rate_mismatch")

    return reasons