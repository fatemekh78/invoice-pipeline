import argparse
import random
from pathlib import Path

from src.extract.evaluate import expected_values
from src.extract.rules import extract_fields
from src.extract.split import list_documents
from src.extract.validate import merge_fields, review_reasons
from src.extract.values import extract_fields_by_value
from src.ocr.evaluate import FIELD_NAMES, load_label
from src.ocr.noise import NOISE_LEVELS, degrade_image
from src.ocr.preprocess import preprocess_image
from src.ocr.read import read_pdf_text

# Fields that decide how an invoice is booked (supplier text is separate)
CRITICAL_FIELDS = ["invoice_number", "invoice_date", "vat_amount", "total"]


def evaluate_review(
    folder: Path,
    language: str,
    split: str = "dev",
    level: str = "clean",
    preprocess=None,
    limit: int | None = None,
) -> dict:
    pdf_files = list_documents(folder, language, split)
    if limit:
        pdf_files = pdf_files[:limit]

    stats = {
        "documents": len(pdf_files),
        "wrong": 0, "wrong_flagged": 0,
        "wrong_critical": 0, "wrong_critical_flagged": 0,
        "fully_correct": 0, "fully_correct_flagged": 0,
        "missing_only": 0,
    }
    silent_examples = []

    for pdf_path in pdf_files:
        label = load_label(pdf_path.with_suffix(".json"))

        # Same file + same level = same damage, so results are reproducible
        rng = random.Random(f"{pdf_path.stem}-{level}")
        ocr_text = read_pdf_text(
            pdf_path,
            language,
            transform=lambda image: degrade_image(image, level, rng),
            preprocess=preprocess,
        )

        merged, reasons = merge_fields(
            extract_fields(ocr_text, language),
            extract_fields_by_value(ocr_text, language),
        )
        reasons = reasons + review_reasons(merged, language)
        flagged = bool(reasons)

        expected = expected_values(label)
        wrong = [n for n in FIELD_NAMES if merged[n] is not None and merged[n] != expected[n]]
        missing = [n for n in FIELD_NAMES if merged[n] is None]
        wrong_critical = [n for n in wrong if n in CRITICAL_FIELDS]

        if wrong:
            stats["wrong"] += 1
            stats["wrong_flagged"] += flagged
        if wrong_critical:
            stats["wrong_critical"] += 1
            stats["wrong_critical_flagged"] += flagged
            if not flagged:
                silent_examples.append(
                    f"{pdf_path.stem}: " + ", ".join(
                        f"{n} expected {expected[n]!r} got {merged[n]!r}" for n in wrong_critical
                    )
                )
        if not wrong and not missing:
            stats["fully_correct"] += 1
            stats["fully_correct_flagged"] += flagged
        if not wrong and missing:
            stats["missing_only"] += 1

    stats["silent_examples"] = silent_examples
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure the review layer (two extractors + checks).")
    parser.add_argument("--folder", default="data/synthetic_varied")
    parser.add_argument("--split", choices=["dev", "test"], default="dev")
    parser.add_argument("--limit", type=int, default=None, help="max invoices per language")
    parser.add_argument("--levels", nargs="+", default=["clean"],
                        choices=list(NOISE_LEVELS), help="noise levels to test")
    parser.add_argument("--preprocess", action="store_true", help="clean the image before OCR")
    args = parser.parse_args()

    if args.split == "test":
        print("NOTE: this is the test set. Run it once, at the very end, and do not tune on it.")

    preprocess = preprocess_image if args.preprocess else None
    print(f"review layer | folder: {args.folder} | split: {args.split} | "
          f"preprocessing: {'on' if args.preprocess else 'off'}")

    for level in args.levels:
        print(f"\n===== noise: {level} =====")
        for language in ("en", "sv", "fi"):
            s = evaluate_review(Path(args.folder), language, args.split, level, preprocess, args.limit)
            print(f"\n{language}: {s['documents']} documents")
            print(f"  invoices with a wrong value (any field):   {s['wrong']:3d}"
                  f"   flagged {s['wrong_flagged']}, SILENT {s['wrong'] - s['wrong_flagged']}")
            print(f"  invoices with a wrong value (number/date/VAT/total): {s['wrong_critical']:3d}"
                  f"   flagged {s['wrong_critical_flagged']}, "
                  f"SILENT {s['wrong_critical'] - s['wrong_critical_flagged']}")
            print(f"  fully correct invoices:                    {s['fully_correct']:3d}"
                  f"   flagged for nothing {s['fully_correct_flagged']}")
            print(f"  only missing fields (all flagged):         {s['missing_only']:3d}")
            for example in s["silent_examples"][:5]:
                print(f"    SILENT {example}")


if __name__ == "__main__":
    main()