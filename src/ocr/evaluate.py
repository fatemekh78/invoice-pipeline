import argparse
import json
import random
from pathlib import Path

from rapidfuzz.distance import Levenshtein

from src.generate.formatting import format_date, format_invoice_text, format_money
from src.ocr.noise import NOISE_LEVELS, degrade_image
from src.ocr.preprocess import preprocess_image
from src.ocr.read import read_pdf_text
from src.schema import InvoiceLabel

FIELD_NAMES = ["supplier", "invoice_number", "invoice_date", "vat_amount", "total"]


def normalize(text: str) -> str:
    # OCR adds extra blank lines and spaces, so compare words only
    return " ".join(text.split())


def load_label(json_path: Path) -> InvoiceLabel:
    return InvoiceLabel(**json.loads(json_path.read_text(encoding="utf-8")))


def expected_text(label: InvoiceLabel) -> str:
    truth = {
        "language": label.language,
        "supplier": label.supplier,
        "invoice_number": label.invoice_number,
        "invoice_date": label.invoice_date.isoformat(),
        "total": label.total,
        "vat_amount": label.vat_amount,
    }
    return format_invoice_text(truth)


def expected_fields(label: InvoiceLabel) -> dict:
    return {
        "supplier": label.supplier,
        "invoice_number": label.invoice_number,
        "invoice_date": format_date(label.invoice_date, label.language),
        "vat_amount": format_money(label.vat_amount, label.language),
        "total": format_money(label.total, label.language),
    }


def evaluate_language(
    folder: Path, language: str, limit: int, level: str = "clean", preprocess=None
) -> dict:
    pdf_files = sorted(Path(folder).glob(f"{language}_*.pdf"))[:limit]

    error_rates = []
    hits = {name: 0 for name in FIELD_NAMES}

    for pdf_path in pdf_files:
        label = load_label(pdf_path.with_suffix(".json"))

        # Same file + same level = same damage, so results are reproducible
        rng = random.Random(f"{pdf_path.stem}-{level}")
        ocr_text = normalize(read_pdf_text(
            pdf_path,
            language,
            transform=lambda image: degrade_image(image, level, rng),
            preprocess=preprocess,
        ))

        expected = normalize(expected_text(label))
        error_rates.append(Levenshtein.normalized_distance(ocr_text, expected))

        for name, value in expected_fields(label).items():
            if normalize(value) in ocr_text:
                hits[name] += 1

    count = len(pdf_files)
    return {
        "documents": count,
        "cer": sum(error_rates) / count if count else 0.0,
        "field_hit_rate": {name: hits[name] / count if count else 0.0 for name in FIELD_NAMES},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure OCR accuracy per language and noise level.")
    parser.add_argument("--folder", default="data/synthetic")
    parser.add_argument("--limit", type=int, default=30, help="invoices per language")
    parser.add_argument("--levels", nargs="+", default=list(NOISE_LEVELS),
                        choices=list(NOISE_LEVELS), help="noise levels to test")
    parser.add_argument("--preprocess", action="store_true", help="clean the image before OCR")
    args = parser.parse_args()

    preprocess = preprocess_image if args.preprocess else None
    print(f"preprocessing: {'on' if args.preprocess else 'off'}")

    for level in args.levels:
        print(f"\n===== noise: {level} =====")
        for language in ("en", "sv", "fi"):
            result = evaluate_language(Path(args.folder), language, args.limit, level, preprocess)
            print(f"\n{language}: {result['documents']} documents, CER = {result['cer']:.4f}")
            for name, rate in result["field_hit_rate"].items():
                print(f"  {name:<15} {rate:.1%}")


if __name__ == "__main__":
    main()