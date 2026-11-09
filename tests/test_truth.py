import random
from decimal import ROUND_HALF_UP

import pytest

from src.generate.truth import CENT, LANGUAGE_SETTINGS, make_invoice_truth
from src.schema import InvoiceLabel


@pytest.mark.parametrize("language", ["en", "sv", "fi"])
def test_generated_truth_matches_invoice_schema(language):
    for seed in range(100):
        truth = make_invoice_truth(language, random.Random(seed))
        InvoiceLabel(**truth)


@pytest.mark.parametrize("language", ["en", "sv", "fi"])
def test_generated_truth_is_reproducible(language):
    first = make_invoice_truth(language, random.Random(42))
    second = make_invoice_truth(language, random.Random(42))

    assert first == second


@pytest.mark.parametrize("language", ["en", "sv", "fi"])
def test_vat_matches_rate(language):
    rate = LANGUAGE_SETTINGS[language]["vat_rate"]
    for seed in range(100):
        truth = make_invoice_truth(language, random.Random(seed))
        net = truth["total"] - truth["vat_amount"]
        assert truth["vat_amount"] == (net * rate).quantize(CENT, rounding=ROUND_HALF_UP)