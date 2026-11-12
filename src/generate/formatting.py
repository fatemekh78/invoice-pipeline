from datetime import date
from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")

SUPPORTED_LANGUAGES = ("en", "sv", "fi")

CURRENCY_SYMBOL = {"en": "£", "sv": "kr", "fi": "€"}

MONTHS_EN = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

LABELS = {
    "en": {"title": "Invoice", "number": "Invoice no.", "date": "Date",
           "vat": "VAT", "total": "Total"},
    "sv": {"title": "Faktura", "number": "Fakturanummer", "date": "Datum",
           "vat": "Moms", "total": "Att betala"},
    "fi": {"title": "Lasku", "number": "Laskun numero", "date": "Päivämäärä",
           "vat": "ALV", "total": "Yhteensä"},
}

def _check_language(language: str) -> None:
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unknown language: {language}")


def format_money(amount: Decimal, language: str) -> str:
    _check_language(language)

    amount = amount.quantize(CENT, rounding=ROUND_HALF_UP)
    formatted_amount = f"{amount:,.2f}"

    if language == "en":
        return f"{CURRENCY_SYMBOL[language]}{formatted_amount}"

    formatted_amount = formatted_amount.translate(str.maketrans({",": " ", ".": ","}))
    return f"{formatted_amount} {CURRENCY_SYMBOL[language]}"


def format_date(value: date, language: str) -> str:
    _check_language(language)

    if language == "en":
        return f"{value.day} {MONTHS_EN[value.month - 1]} {value.year}"
    if language == "sv":
        return value.isoformat()
    return f"{value.day}.{value.month}.{value.year}"

def format_invoice_text(truth: dict) -> str:
    language = truth["language"]
    _check_language(language)
    labels = LABELS[language]

    invoice_date = date.fromisoformat(truth["invoice_date"])

    lines = [
        labels["title"],
        truth["supplier"],
        "",
        f"{labels['number']}: {truth['invoice_number']}",
        f"{labels['date']}: {format_date(invoice_date, language)}",
        f"{labels['vat']}: {format_money(truth['vat_amount'], language)}",
        f"{labels['total']}: {format_money(truth['total'], language)}",
    ]

    return "\n".join(lines)