from datetime import date
from decimal import Decimal

from src.extract.evaluate import FIELD_NAMES, evaluate_extraction, expected_values
from src.generate.build_dataset import build_dataset
from src.schema import InvoiceLabel


def test_expected_values_match_the_label():
    label = InvoiceLabel(
        doc_type="invoice", language="fi", supplier="Koivu Palvelut Oy",
        invoice_number="10234", invoice_date="2026-09-04", currency="EUR",
        total="1245.50", vat_amount="249.10",
    )

    values = expected_values(label)

    assert values["supplier"] == "Koivu Palvelut Oy"
    assert values["invoice_date"] == date(2026, 9, 4)
    assert values["total"] == Decimal("1245.50")


def test_evaluate_extraction_returns_sensible_numbers(tmp_path):
    build_dataset(tmp_path, count_per_language=2, base_seed=1)

    result = evaluate_extraction(tmp_path, "fi", split="dev", level="clean")

    assert result["documents"] == 2
    assert set(result["field_accuracy"]) == set(FIELD_NAMES)
    assert all(0.0 <= rate <= 1.0 for rate in result["field_accuracy"].values())