from datetime import date
from decimal import Decimal

import pytest

from src.generate.formatting import format_date, format_invoice_text, format_money


@pytest.mark.parametrize("amount, language, expected", [
    (Decimal("1245.50"), "en", "£1,245.50"),
    (Decimal("1245.50"), "sv", "1 245,50 kr"),
    (Decimal("1245.50"), "fi", "1 245,50 €"),
    (Decimal("0.05"), "fi", "0,05 €"),
    (Decimal("1000000.00"), "sv", "1 000 000,00 kr"),
])
def test_format_money(amount, language, expected):
    assert format_money(amount, language) == expected


def test_format_money_adds_missing_decimals():
    assert format_money(Decimal("1245.5"), "en") == "£1,245.50"


def test_format_money_unknown_language():
    with pytest.raises(ValueError):
        format_money(Decimal("1.00"), "de")


@pytest.mark.parametrize("d, language, expected", [
    (date(2026, 9, 14), "en", "14 September 2026"),
    (date(2026, 9, 4), "en", "4 September 2026"),
    (date(2026, 9, 4), "sv", "2026-09-04"),
    (date(2026, 9, 4), "fi", "4.9.2026"),
    (date(2026, 12, 31), "fi", "31.12.2026"),
])
def test_format_date(d, language, expected):
    assert format_date(d, language) == expected


def test_format_date_unknown_language():
    with pytest.raises(ValueError):
        format_date(date(2026, 9, 14), "de")


def test_format_invoice_text_swedish():
    truth = {
        "doc_type": "invoice",
        "language": "sv",
        "supplier": "Björk Handel AB",
        "invoice_number": "10234",
        "invoice_date": "2026-09-04",
        "currency": "SEK",
        "total": Decimal("1245.50"),
        "vat_amount": Decimal("249.10"),
    }

    text = format_invoice_text(truth)

    assert "Faktura" in text
    assert "Björk Handel AB" in text
    assert "Fakturanummer: 10234" in text
    assert "Datum: 2026-09-04" in text
    assert "Moms: 249,10 kr" in text
    assert "Att betala: 1 245,50 kr" in text


def test_format_invoice_text_finnish():
    truth = {
        "doc_type": "invoice",
        "language": "fi",
        "supplier": "Koivu Palvelut Oy",
        "invoice_number": "10234",
        "invoice_date": "2026-09-04",
        "currency": "EUR",
        "total": Decimal("1245.50"),
        "vat_amount": Decimal("249.10"),
    }

    text = format_invoice_text(truth)

    assert "Lasku" in text
    assert "Koivu Palvelut Oy" in text
    assert "Laskun numero: 10234" in text
    assert "Päivämäärä: 4.9.2026" in text
    assert "ALV: 249,10 €" in text
    assert "Yhteensä: 1 245,50 €" in text


def test_format_invoice_text_english():
    truth = {
        "doc_type": "invoice",
        "language": "en",
        "supplier": "Oak Supply Ltd",
        "invoice_number": "10234",
        "invoice_date": "2026-09-04",
        "currency": "GBP",
        "total": Decimal("1245.50"),
        "vat_amount": Decimal("249.10"),
    }

    text = format_invoice_text(truth)

    assert "Invoice" in text
    assert "Oak Supply Ltd" in text
    assert "Invoice no.: 10234" in text
    assert "Date: 4 September 2026" in text
    assert "VAT: £249.10" in text
    assert "Total: £1,245.50" in text


def test_format_invoice_text_unknown_language():
    with pytest.raises(ValueError):
        format_invoice_text({"language": "de"})