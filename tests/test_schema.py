import pytest
from pydantic import ValidationError
from src.schema import InvoiceLabel

def test_valid_invoice_is_accepted():
    InvoiceLabel(
        doc_type="invoice",
        language="fi",
        supplier="Example Oy",
        invoice_number="10234",
        invoice_date="2026-09-14",
        currency="EUR",
        total="1245.50",
        vat_amount="249.10",
    )

def test_unknown_currency_is_rejected():
    with pytest.raises(ValidationError):
        InvoiceLabel(
            doc_type="invoice",
            language="fi",
            supplier="Example Oy",
            invoice_number="10234",
            invoice_date="2026-09-14",
            currency="USD",
            total="1245.50",
            vat_amount="249.10",
        )

def test_vat_amount_more_than_total_is_rejected():
    with pytest.raises(ValidationError):
        InvoiceLabel(
            doc_type="invoice",
            language="fi",
            supplier="Example Oy",
            invoice_number="10234",
            invoice_date="2026-09-14",
            currency="EUR",          # valid
            total="1245.50",
            vat_amount="1245.51",    # the only wrong value
        )


def test_empty_supplier_is_rejected():
    with pytest.raises(ValidationError):
        InvoiceLabel(
            doc_type="invoice",
            language="fi",
            supplier="",             # the only wrong value
            invoice_number="10234",
            invoice_date="2026-09-14",
            currency="EUR",          # valid
            total="1245.50",
            vat_amount="249.10",
        )


def test_invalid_invoice_date_is_rejected():
    with pytest.raises(ValidationError):
        InvoiceLabel(
            doc_type="invoice",
            language="fi",
            supplier="Example Oy",   # valid
            invoice_number="10234",
            invoice_date="2026-00-14",   # the only wrong value
            currency="EUR",          # valid
            total="1245.50",
            vat_amount="249.10",
        )
