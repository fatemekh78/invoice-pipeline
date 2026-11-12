import pytest

from src.generate.pdf import LAYOUTS, render_invoice_pdf

SAMPLE = "Lasku\nKoivu Palvelut Oy\n\nYhteensä: 1 245,50 €"


def test_render_invoice_pdf_creates_a_pdf_file(tmp_path):
    output = tmp_path / "invoice.pdf"

    render_invoice_pdf(SAMPLE, output)

    assert output.exists()
    assert output.read_bytes().startswith(b"%PDF")


@pytest.mark.parametrize("layout", LAYOUTS, ids=lambda layout: layout["name"])
def test_every_layout_creates_a_pdf_file(tmp_path, layout):
    output = tmp_path / "invoice.pdf"

    render_invoice_pdf(SAMPLE, output, layout)

    assert output.read_bytes().startswith(b"%PDF")
