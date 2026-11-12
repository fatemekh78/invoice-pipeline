from src.generate.pdf import render_invoice_pdf


def test_render_invoice_pdf_creates_a_pdf_file(tmp_path):
    output = tmp_path / "invoice.pdf"

    render_invoice_pdf("Lasku\nKoivu Palvelut Oy\n\nYhteensä: 1 245,50 €", output)

    assert output.exists()
    assert output.read_bytes().startswith(b"%PDF")
    