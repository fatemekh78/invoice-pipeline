from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

# Project root = two folders above this file (src/generate/pdf.py)
FONT_DIR = Path(__file__).resolve().parents[2] / "assets" / "fonts"

pdfmetrics.registerFont(TTFont("DejaVu", str(FONT_DIR / "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DejaVu-Bold", str(FONT_DIR / "DejaVuSans-Bold.ttf")))

LAYOUTS = [
    {"name": "classic", "margin_x": 60, "top": 80, "title_size": 22,
     "supplier_size": 14, "body_size": 12, "line_gap": 22, "title_align": "left"},
    {"name": "centered", "margin_x": 80, "top": 120, "title_size": 28,
     "supplier_size": 16, "body_size": 11, "line_gap": 26, "title_align": "center"},
    {"name": "compact", "margin_x": 40, "top": 50, "title_size": 18,
     "supplier_size": 12, "body_size": 10, "line_gap": 16, "title_align": "right"},
      {"name": "large", "margin_x": 70, "top": 100, "title_size": 30,
     "supplier_size": 18, "body_size": 14, "line_gap": 34, "title_align": "left"},
]


def _draw(pdf, text, align, margin_x, page_width, y):
    if align == "center":
        pdf.drawCentredString(page_width / 2, y, text)
    elif align == "right":
        pdf.drawRightString(page_width - margin_x, y, text)
    else:
        pdf.drawString(margin_x, y, text)


def render_invoice_pdf(text: str, output_path: Path, layout: dict | None = None) -> None:
    layout = layout or LAYOUTS[0]
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    page_width, page_height = A4
    pdf = canvas.Canvas(str(output_path), pagesize=A4)

    margin_x = layout["margin_x"]
    y = page_height - layout["top"]  # PDF coordinates start at the BOTTOM

    for index, line in enumerate(text.split("\n")):
        if index == 0:      # title
            pdf.setFont("DejaVu-Bold", layout["title_size"])
            _draw(pdf, line, layout["title_align"], margin_x, page_width, y)
            y -= layout["title_size"] * 1.6
        elif index == 1:    # supplier
            pdf.setFont("DejaVu-Bold", layout["supplier_size"])
            _draw(pdf, line, layout["title_align"], margin_x, page_width, y)
            y -= layout["supplier_size"] * 2
        elif line == "":    # empty line = extra space
            y -= layout["line_gap"] * 0.6
        else:               # details
            pdf.setFont("DejaVu", layout["body_size"])
            pdf.drawString(margin_x, y, line)
            y -= layout["line_gap"]

    pdf.save()