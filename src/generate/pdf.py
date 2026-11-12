from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

# Project root = two folders above this file (src/generate/pdf.py)
FONT_DIR = Path(__file__).resolve().parents[2] / "assets" / "fonts"

pdfmetrics.registerFont(TTFont("DejaVu", str(FONT_DIR / "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DejaVu-Bold", str(FONT_DIR / "DejaVuSans-Bold.ttf")))


def render_invoice_pdf(text: str, output_path: Path) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    _, page_height = A4
    pdf = canvas.Canvas(str(output_path), pagesize=A4)

    x = 60
    y = page_height - 80  # PDF coordinates start at the BOTTOM, so we start high

    for index, line in enumerate(text.split("\n")):
        if index == 0:      # title
            pdf.setFont("DejaVu-Bold", 22)
            pdf.drawString(x, y, line)
            y -= 36
        elif index == 1:    # supplier
            pdf.setFont("DejaVu-Bold", 14)
            pdf.drawString(x, y, line)
            y -= 30
        elif line == "":    # empty line = extra space
            y -= 14
        else:               # details
            pdf.setFont("DejaVu", 12)
            pdf.drawString(x, y, line)
            y -= 22

    pdf.save()