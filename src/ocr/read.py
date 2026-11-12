from pathlib import Path

import pymupdf  # PyMuPDF: turns a PDF page into an image
import pytesseract
from PIL import Image

# Tell Python where Tesseract is installed, so we don't depend on the PATH
TESSERACT_EXE = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
if TESSERACT_EXE.exists():
    pytesseract.pytesseract.tesseract_cmd = str(TESSERACT_EXE)

# Our language codes -> Tesseract language names
TESSERACT_LANGUAGE = {"en": "eng", "sv": "swe", "fi": "fin"}


def pdf_to_image(pdf_path: Path, dpi: int = 200) -> Image.Image:
    with pymupdf.open(str(pdf_path)) as document:
        pixmap = document[0].get_pixmap(dpi=dpi)  # first page only
        return Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)


def read_pdf_text(pdf_path: Path, language: str, transform=None) -> str:
    if language not in TESSERACT_LANGUAGE:
        raise ValueError(f"Unknown language: {language}")

    image = pdf_to_image(pdf_path)
    if transform is not None:
        image = transform(image)  # e.g. add noise before OCR
    return pytesseract.image_to_string(image, lang=TESSERACT_LANGUAGE[language])