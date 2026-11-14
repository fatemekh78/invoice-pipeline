from pathlib import Path

from src.extract.rules import extract_fields
from src.extract.validate import merge_fields, review_reasons
from src.extract.values import extract_fields_by_value
from src.ocr.preprocess import preprocess_image
from src.ocr.read import read_pdf_text


def _to_text(value) -> str | None:
    if value is None:
        return None
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def process_pdf(pdf_path: Path, language: str, preprocess: bool = True) -> dict:
    text = read_pdf_text(
        pdf_path, language, preprocess=preprocess_image if preprocess else None
    )

    merged, disagreements = merge_fields(
        extract_fields(text, language),
        extract_fields_by_value(text, language),
    )
    reasons = disagreements + review_reasons(merged, language)

    return {
        "language": language,
        "fields": {name: _to_text(value) for name, value in merged.items()},
        "review_reasons": reasons,
        "needs_review": bool(reasons),
    }