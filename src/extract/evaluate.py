import argparse
import random
from pathlib import Path

from src.extract.rules import extract_fields
from src.extract.split import list_documents
from src.extract.values import extract_fields_by_value
from src.ocr.evaluate import FIELD_NAMES, load_label
from src.ocr.noise import NOISE_LEVELS, degrade_image
from src.ocr.preprocess import preprocess_image
from src.ocr.read import read_pdf_text
from src.schema import InvoiceLabel

EXTRACTORS = {"rules": extract_fields, "values": extract_fields_by_value}


def expected_values(label: InvoiceLabel) -> dict:
    return {
        "supplier": label.supplier,
        "invoice_number": label.invoice_number,
        "invoice_date": label.invoice_date,
        "vat_amount": label.vat_amount,
        "total": label.total,
    }


def evaluate_extraction(
    folder: Path,
    language: str,
    split: str = "dev",
    level: str = "clean",
    preprocess=None,
    limit: int | None = None,
    extractor=extract_fields,
) -> dict:
    pdf_files = list_documents(folder, language, split)
    if limit:
        pdf_files = pdf_files[:limit]

    correct = {name: 0 for name in FIELD_NAMES}
    missing = {name: 0 for name in FIELD_NAMES}  # extractor returned None (safe)
    wrong = {name: 0 for name in FIELD_NAMES}    # extractor returned a wrong value (dangerous)
    failures = []

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

        extracted = extractor(ocr_text, language)
        expected = expected_values(label)

        for name in FIELD_NAMES:
            if extracted[name] == expected[name]:
                correct[name] += 1
                continue

            kind = "MISSING" if extracted[name] is None else "WRONG"
            if kind == "MISSING":
                missing[name] += 1
            else:
                wrong[name] += 1
            failures.append({
                "kind": kind,
                "document": pdf_path.stem,
                "field": name,
                "expected": expected[name],
                "got": extracted[name],
            })

    count = len(pdf_files)

    def rate(counter: dict) -> dict:
        return {name: counter[name] / count if count else 0.0 for name in FIELD_NAMES}

    return {
        "documents": count,
        "field_accuracy": rate(correct),
        "field_missing": rate(missing),
        "field_wrong": rate(wrong),
        "failures": failures,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure field extraction accuracy (OCR + extractor).")
    parser.add_argument("--folder", default="data/synthetic_varied")
    parser.add_argument("--split", choices=["dev", "test"], default="dev")
    parser.add_argument("--limit", type=int, default=None, help="max invoices per language")
    parser.add_argument("--levels", nargs="+", default=["clean"],
                        choices=list(NOISE_LEVELS), help="noise levels to test")
    parser.add_argument("--preprocess", action="store_true", help="clean the image before OCR")
    parser.add_argument("--extractor", choices=list(EXTRACTORS), default="rules")
    parser.add_argument("--show-failures", type=int, default=5,
                        help="failures to print per language (0 = none)")
    args = parser.parse_args()

    if args.split == "test":
        print("NOTE: this is the test set. Run it once, at the very end, and do not tune on it.")

    preprocess = preprocess_image if args.preprocess else None
    print(f"extractor: {args.extractor} | folder: {args.folder} | split: {args.split} | "
          f"preprocessing: {'on' if args.preprocess else 'off'}")

    for level in args.levels:
        print(f"\n===== noise: {level} =====")
        for language in ("en", "sv", "fi"):
            result = evaluate_extraction(
                Path(args.folder), language, args.split, level, preprocess,
                args.limit, EXTRACTORS[args.extractor],
            )
            print(f"\n{language}: {result['documents']} documents "
                  f"(correct / missing / WRONG)")
            for name in FIELD_NAMES:
                print(f"  {name:<15} {result['field_accuracy'][name]:6.1%}"
                      f"  {result['field_missing'][name]:6.1%}"
                      f"  {result['field_wrong'][name]:6.1%}")

            for failure in result["failures"][: args.show_failures]:
                print(f"    {failure['kind']} {failure['document']} {failure['field']}: "
                      f"expected {failure['expected']!r}, got {failure['got']!r}")


if __name__ == "__main__":
    main()