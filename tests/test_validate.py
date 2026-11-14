import random
from datetime import date
from decimal import Decimal

import pytest

from src.extract.validate import merge_fields, review_reasons
from src.generate.truth import make_invoice_truth


def fields_from_truth(truth: dict) -> dict:
    return {
        "supplier": truth["supplier"],
        "invoice_number": truth["invoice_number"],
        "invoice_date": date.fromisoformat(truth["invoice_date"]),
        "vat_amount": truth["vat_amount"],
        "total": truth["total"],
    }


def test_merge_keeps_agreeing_values():
    merged, reasons = merge_fields({"total": Decimal("10.00")}, {"total": Decimal("10.00")})

    assert merged == {"total": Decimal("10.00")}
    assert reasons == []


def test_merge_takes_the_value_when_the_other_extractor_found_nothing():
    merged, reasons = merge_fields({"total": None}, {"total": Decimal("10.00")})

    assert merged == {"total": Decimal("10.00")}
    assert reasons == []


def test_merge_refuses_to_pick_when_extractors_disagree():
    merged, reasons = merge_fields({"total": Decimal("10.00")}, {"total": Decimal("20.00")})

    assert merged == {"total": None}
    assert reasons == ["extractors_disagree:total"]


@pytest.mark.parametrize("language", ["en", "sv", "fi"])
def test_correct_invoices_are_never_flagged(language):
    for seed in range(200):
        truth = make_invoice_truth(language, random.Random(seed))

        assert review_reasons(fields_from_truth(truth), language) == []


def test_missing_field_is_flagged():
    truth = make_invoice_truth("fi", random.Random(1))
    fields = fields_from_truth(truth)
    fields["total"] = None

    assert "missing:total" in review_reasons(fields, "fi")


def test_vat_above_total_is_flagged():
    truth = make_invoice_truth("en", random.Random(1))
    fields = fields_from_truth(truth)
    fields["vat_amount"], fields["total"] = fields["total"], fields["vat_amount"]

    assert "vat_above_total" in review_reasons(fields, "en")


def test_total_one_hundred_times_too_large_is_flagged():
    truth = make_invoice_truth("en", random.Random(1))
    fields = fields_from_truth(truth)
    fields["total"] = fields["total"] * 100

    assert "vat_rate_mismatch" in review_reasons(fields, "en")


def test_one_cent_error_in_vat_is_flagged_with_zero_tolerance():
    truth = make_invoice_truth("sv", random.Random(2))
    fields = fields_from_truth(truth)
    fields["vat_amount"] = fields["vat_amount"] - Decimal("0.01")

    assert "vat_rate_mismatch" in review_reasons(fields, "sv")


def test_unknown_language_is_rejected():
    with pytest.raises(ValueError):
        review_reasons({}, "de")