import random

import pytest
from fastapi.testclient import TestClient

from src.api import app
from src.generate.formatting import format_invoice_text
from src.generate.pdf import render_invoice_pdf
from src.generate.truth import make_invoice_truth

client = TestClient(app)


def make_pdf(tmp_path, text: str) -> bytes:
    path = tmp_path / "invoice.pdf"
    render_invoice_pdf(text, path)
    return path.read_bytes()


def post_pdf(pdf: bytes, language: str):
    return client.post(
        "/extract",
        files={"file": ("invoice.pdf", pdf, "application/pdf")},
        data={"language": language},
    )


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


@pytest.mark.parametrize("language", ["en", "sv", "fi"])
def test_extract_returns_the_fields_of_a_clean_invoice(tmp_path, language):
    truth = make_invoice_truth(language, random.Random(1))
    pdf = make_pdf(tmp_path, format_invoice_text(truth))

    response = post_pdf(pdf, language)

    assert response.status_code == 200
    body = response.json()
    assert body["fields"]["supplier"] == truth["supplier"]
    assert body["fields"]["invoice_number"] == truth["invoice_number"]
    assert body["fields"]["invoice_date"] == truth["invoice_date"]
    assert body["fields"]["vat_amount"] == str(truth["vat_amount"])  # money as text
    assert body["fields"]["total"] == str(truth["total"])
    assert body["needs_review"] is False
    assert body["review_reasons"] == []


def test_incomplete_invoice_is_flagged_for_review(tmp_path):
    pdf = make_pdf(tmp_path, "Lasku\nKoivu Palvelut Oy")

    body = post_pdf(pdf, "fi").json()

    assert body["fields"]["supplier"] == "Koivu Palvelut Oy"
    assert body["fields"]["total"] is None
    assert body["needs_review"] is True
    assert "missing:total" in body["review_reasons"]


def test_file_that_is_not_a_pdf_is_rejected():
    response = post_pdf(b"just some text", "fi")

    assert response.status_code == 400


def test_unknown_language_is_rejected(tmp_path):
    pdf = make_pdf(tmp_path, "Lasku\nKoivu Palvelut Oy")

    assert post_pdf(pdf, "de").status_code == 400


def test_file_that_is_too_large_is_rejected(monkeypatch):
    monkeypatch.setattr("src.api.MAX_UPLOAD_BYTES", 10)

    response = post_pdf(b"%PDF" + b"x" * 100, "fi")

    assert response.status_code == 413


def test_broken_pdf_gives_a_clean_error():
    response = post_pdf(b"%PDF-1.4 this is not a real pdf", "fi")

    assert response.status_code == 422