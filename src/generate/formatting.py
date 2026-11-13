import random
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")

SUPPORTED_LANGUAGES = ("en", "sv", "fi")

CURRENCY_SYMBOL = {"en": "£", "sv": "kr", "fi": "€"}

MONTHS_EN = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

# Several ways to write each label. The FIRST variant is the standard one.
LABEL_VARIANTS = {
    "en": {
        "title": ["Invoice"],
        "number": ["Invoice no.", "Invoice number", "Ref", "Invoice #"],
        "date": ["Date", "Invoice date", "Issued"],
        "vat": ["VAT", "VAT amount", "VAT total"],
        "total": ["Total", "Amount due", "Grand total", "Balance to pay"],
    },
    "sv": {
        "title": ["Faktura"],
        "number": ["Fakturanummer", "Fakturanr", "Ref"],
        "date": ["Datum", "Fakturadatum"],
        "vat": ["Moms", "Varav moms"],
        "total": ["Att betala", "Totalt", "Summa att betala"],
    },
    "fi": {
        "title": ["Lasku"],
        "number": ["Laskun numero", "Laskunro", "Laskunumero"],
        "date": ["Päivämäärä", "Laskun päivämäärä", "Päiväys"],
        "vat": ["ALV", "ALV yhteensä", "Arvonlisävero"],
        "total": ["Yhteensä", "Maksettava yhteensä", "Loppusumma"],
    },
}

# The standard labels = the first variant of each
LABELS = {
    language: {key: values[0] for key, values in options.items()}
    for language, options in LABEL_VARIANTS.items()
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


def format_invoice_text(truth: dict, rng: random.Random | None = None) -> str:
    language = truth["language"]
    _check_language(language)

    if rng is None:
        labels = LABELS[language]  # standard labels, standard order
    else:
        labels = {key: rng.choice(values) for key, values in LABEL_VARIANTS[language].items()}

    invoice_date = date.fromisoformat(truth["invoice_date"])

    details = [
        f"{labels['number']}: {truth['invoice_number']}",
        f"{labels['date']}: {format_date(invoice_date, language)}",
        f"{labels['vat']}: {format_money(truth['vat_amount'], language)}",
        f"{labels['total']}: {format_money(truth['total'], language)}",
    ]
    if rng is not None:
        rng.shuffle(details)  # the four detail lines come in a random order

    lines = [labels["title"], truth["supplier"], ""] + details
    return "\n".join(lines)