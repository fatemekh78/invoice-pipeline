from src.generate.pdf import render_invoice_pdf
from src.ocr.read import read_pdf_text


def test_read_pdf_text_finds_the_supplier_name(tmp_path):
    pdf_path = tmp_path / "invoice.pdf"
    render_invoice_pdf("Lasku\nKoivu Palvelut Oy\n\nLaskun numero: 10234", pdf_path)

    text = read_pdf_text(pdf_path, "fi")

    assert "Koivu Palvelut Oy" in text
    assert "10234" in text


def test_read_pdf_text_unknown_language(tmp_path):
    pdf_path = tmp_path / "invoice.pdf"
    render_invoice_pdf("Lasku", pdf_path)

    import pytest
    with pytest.raises(ValueError):
        read_pdf_text(pdf_path, "de")