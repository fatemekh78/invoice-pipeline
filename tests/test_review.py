from datetime import date
from decimal import Decimal

import pytest

from src.review import build_review_record, describe_reason, parse_corrections

GOOD = {
    "supplier": "Koivu Palvelut Oy",
    "invoice_number": "10234",
    "invoice_date": "2026-09-04",
    "vat_amount": "249.10",
    "total": "1245.50",
}


def test_parse_corrections_turns_text_into_typed_values():
    fields, errors = parse_corrections(GOOD)

    assert errors == []
    assert fields["invoice_date"] == date(2026, 9, 4)
    assert fields["total"] == Decimal("1245.50")
    assert fields["invoice_number"] == "10234"


def test_parse_corrections_empty_text_means_no_value():
    fields, errors = parse_corrections({**GOOD, "total": "  "})

    assert errors == []
    assert fields["total"] is None


@pytest.mark.parametrize("bad_total", ["12,50", "abc", "NaN", "-5", "1.234", "۱۲۳"])
def test_parse_corrections_rejects_bad_money(bad_total):
    _, errors = parse_corrections({**GOOD, "total": bad_total})

    assert len(errors) == 1


@pytest.mark.parametrize("bad_date", ["4.9.2026", "2026-13-45", "20260904", "yesterday"])
def test_parse_corrections_rejects_bad_dates(bad_date):
    _, errors = parse_corrections({**GOOD, "invoice_date": bad_date})

    assert len(errors) == 1


def test_build_review_record_lists_what_the_reviewer_changed():
    corrected, _ = parse_corrections({**GOOD, "total": "1245.51"})

    record = build_review_record("fi", GOOD, corrected)

    assert record["changed_fields"] == ["total"]
    assert record["original"]["total"] == "1245.50"
    assert record["corrected"]["total"] == "1245.51"


def test_build_review_record_without_changes():
    corrected, _ = parse_corrections(GOOD)

    record = build_review_record("fi", GOOD, corrected)

    assert record["changed_fields"] == []


def test_record_keeps_the_remaining_review_reasons():
    corrected, _ = parse_corrections({**GOOD, "total": ""})

    record = build_review_record("fi", GOOD, corrected)

    assert "missing:total" in record["remaining_review_reasons"]


@pytest.mark.parametrize("reason, expected", [
    ("missing:total", "Total was not found."),
    ("missing:invoice_date", "Date was not found."),
    ("extractors_disagree:vat_amount", "The two methods read different values for VAT amount."),
    ("vat_above_total", "VAT is larger than the total."),
    ("vat_rate_mismatch", "VAT does not match the expected rate for this total."),
])
def test_describe_reason(reason, expected):
    assert describe_reason(reason) == expected