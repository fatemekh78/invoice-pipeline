from datetime import date
from decimal import Decimal

import pytest

from src.extract.parse import parse_date, parse_money
from src.generate.formatting import format_date, format_money


@pytest.mark.parametrize("text, language, expected", [
    ("£1,245.50", "en", Decimal("1245.50")),
    ("1 245,50 kr", "sv", Decimal("1245.50")),
    ("1 245,50 €", "fi", Decimal("1245.50")),
    ("0,05 €", "fi", Decimal("0.05")),
    ("1 000 000,00 kr", "sv", Decimal("1000000.00")),
])
def test_parse_money(text, language, expected):
    assert parse_money(text, language) == expected


@pytest.mark.parametrize("language", ["en", "sv", "fi"])
def test_parse_money_undoes_format_money(language):
    for amount in (Decimal("0.05"), Decimal("12.00"), Decimal("1245.50"), Decimal("987654.32")):
        assert parse_money(format_money(amount, language), language) == amount


def test_parse_money_without_a_number_is_rejected():
    with pytest.raises(ValueError):
        parse_money("kr", "sv")


@pytest.mark.parametrize("text, language, expected", [
    ("4 September 2026", "en", date(2026, 9, 4)),
    ("2026-09-04", "sv", date(2026, 9, 4)),
    ("4.9.2026", "fi", date(2026, 9, 4)),
    ("31.12.2026", "fi", date(2026, 12, 31)),
])
def test_parse_date(text, language, expected):
    assert parse_date(text, language) == expected


@pytest.mark.parametrize("language", ["en", "sv", "fi"])
def test_parse_date_undoes_format_date(language):
    for value in (date(2026, 1, 1), date(2026, 9, 4), date(2026, 12, 31)):
        assert parse_date(format_date(value, language), language) == value


def test_parse_date_without_a_date_is_rejected():
    with pytest.raises(ValueError):
        parse_date("no date here", "fi")