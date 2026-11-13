import random
from datetime import date

import pytest

from src.extract.values import extract_fields_by_value
from src.generate.formatting import HOLDOUT_LABEL_VARIANTS, format_invoice_text
from src.generate.truth import make_invoice_truth


@pytest.mark.parametrize("variants", [None, HOLDOUT_LABEL_VARIANTS], ids=["dev-labels", "held-out-labels"])
@pytest.mark.parametrize("language", ["en", "sv", "fi"])
def test_extracts_every_field_whatever_the_label_words(language, variants):
    for seed in range(200):
        truth = make_invoice_truth(language, random.Random(seed))
        text = format_invoice_text(truth, random.Random(seed + 1000), variants)

        fields = extract_fields_by_value(text, language)

        assert fields["supplier"] == truth["supplier"]
        assert fields["invoice_number"] == truth["invoice_number"]
        assert fields["invoice_date"] == date.fromisoformat(truth["invoice_date"])
        assert fields["vat_amount"] == truth["vat_amount"]
        assert fields["total"] == truth["total"]


def test_one_amount_is_ambiguous_so_both_amounts_are_none():
    fields = extract_fields_by_value("Lasku\nKoivu Palvelut Oy\n\nYhteensä: 1 245,50 €", "fi")

    assert fields["supplier"] == "Koivu Palvelut Oy"
    assert fields["total"] is None
    assert fields["vat_amount"] is None


def test_two_dates_are_ambiguous_so_the_date_is_none():
    text = "Lasku\nKoivu Palvelut Oy\n\nA: 4.9.2026\nB: 5.9.2026"

    assert extract_fields_by_value(text, "fi")["invoice_date"] is None


def test_unknown_language_is_rejected():
    with pytest.raises(ValueError):
        extract_fields_by_value("anything", "de")