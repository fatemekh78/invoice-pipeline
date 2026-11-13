import random
from datetime import date

import pytest

from src.extract.rules import extract_fields
from src.generate.formatting import format_invoice_text
from src.generate.truth import make_invoice_truth


@pytest.mark.parametrize("language", ["en", "sv", "fi"])
def test_extracts_every_field_from_perfect_text(language):
    for seed in range(50):
        truth = make_invoice_truth(language, random.Random(seed))
        text = format_invoice_text(truth)

        fields = extract_fields(text, language)

        assert fields["supplier"] == truth["supplier"]
        assert fields["invoice_number"] == truth["invoice_number"]
        assert fields["invoice_date"] == date.fromisoformat(truth["invoice_date"])
        assert fields["vat_amount"] == truth["vat_amount"]
        assert fields["total"] == truth["total"]


@pytest.mark.parametrize("language", ["en", "sv", "fi"])
def test_survives_blank_lines_and_extra_spaces(language):
    truth = make_invoice_truth(language, random.Random(3))
    text = format_invoice_text(truth)
    messy = "\n\n".join(text.split("\n")).replace(": ", ":   ")

    fields = extract_fields(messy, language)

    assert fields["supplier"] == truth["supplier"]
    assert fields["total"] == truth["total"]


def test_missing_fields_are_none_not_guesses():
    fields = extract_fields("Lasku\nKoivu Palvelut Oy", "fi")

    assert fields["supplier"] == "Koivu Palvelut Oy"
    assert fields["invoice_number"] is None
    assert fields["invoice_date"] is None
    assert fields["vat_amount"] is None
    assert fields["total"] is None


def test_unknown_language_is_rejected():
    with pytest.raises(ValueError):
        extract_fields("anything", "de")