import random
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

# Settings per language. The VAT rates are only for synthetic data.
LANGUAGE_SETTINGS = {
    "fi": {"currency": "EUR", "vat_rate": Decimal("0.255"),
           "name_starts": ["Koivu", "Aalto", "Harju", "Niemi", "Virta",
                        "Salo", "Laine", "Kallio", "Rinne", "Nordic"],
        "business_words": ["Palvelut", "Kauppa", "Logistiikka", "Tekniikka",
                           "Rakennus", "Konsultointi", "Huolto", "Tukku"],
        "suffix": "Oy",
    },
    "sv": {
        "currency": "SEK",
        "vat_rate": Decimal("0.25"),
        "name_starts": ["Björk", "Strand", "Ek", "Sjö", "Berg",
                        "Dal", "Holm", "Vik", "Lund", "Nordic"],
        "business_words": ["Tjänster", "Handel", "Logistik", "Teknik",
                           "Bygg", "Konsult", "Service", "Partihandel"],
        "suffix": "AB",
    },
    "en": {
        "currency": "GBP",
        "vat_rate": Decimal("0.20"),
        "name_starts": ["Oak", "Harbour", "Ridge", "Summit", "Willow",
                        "Fairfield", "Stone", "Bright", "Kestrel", "Nordic"],
        "business_words": ["Services", "Supply", "Trading", "Logistics",
                           "Solutions", "Consulting", "Engineering", "Maintenance"],
        "suffix": "Ltd",
    },
}

CENT = Decimal("0.01")

def make_supplier_name(settings: dict, rng: random.Random) -> str:
    start = rng.choice(settings["name_starts"])
    word = rng.choice(settings["business_words"])
    return f"{start} {word} {settings['suffix']}"

def make_invoice_truth(language: str, rng: random.Random) -> dict:
    settings = LANGUAGE_SETTINGS[language]

    supplier = make_supplier_name(settings, rng)
    invoice_number = str(rng.randint(10000, 99999))
    invoice_date = date(2026, 1, 1) + timedelta(days=rng.randint(0, 364))
    net = (Decimal(rng.randint(5000, 500000)) / Decimal("100")).quantize(CENT)
    vat = (net * settings["vat_rate"]).quantize(
        CENT, rounding=ROUND_HALF_UP
    )
    total = net + vat

    return {
        "doc_type": "invoice",
        "language": language,
        "supplier": supplier,
        "invoice_number": invoice_number,
        "invoice_date": invoice_date.isoformat(),
        "currency": settings["currency"],
        "total": total,
        "vat_amount": vat,
    }