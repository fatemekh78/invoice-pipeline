import argparse
import json
import random
from pathlib import Path

from src.generate.formatting import format_invoice_text
from src.generate.pdf import LAYOUTS, render_invoice_pdf
from src.generate.truth import LANGUAGE_SETTINGS, make_invoice_truth
from src.schema import InvoiceLabel


def build_dataset(output_dir: Path, count_per_language: int, base_seed: int = 0) -> int:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    created = 0
    for language in LANGUAGE_SETTINGS:
        for number in range(1, count_per_language + 1):
            # The same text seed always gives the same invoice
            rng = random.Random(f"{base_seed}-{language}-{number}")

            truth = make_invoice_truth(language, rng)
            layout = rng.choice(LAYOUTS)
            doc_id = f"{language}_{number:04d}"

            render_invoice_pdf(format_invoice_text(truth), output_dir / f"{doc_id}.pdf", layout)

            label = InvoiceLabel(**truth).model_dump(mode="json")
            (output_dir / f"{doc_id}.json").write_text(
                json.dumps(label, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            created += 1

    return created


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic invoices (PDF + JSON).")
    parser.add_argument("--count", type=int, default=100, help="invoices per language")
    parser.add_argument("--out", default="data/synthetic", help="output folder")
    args = parser.parse_args()

    total = build_dataset(Path(args.out), args.count)
    print(f"Created {total} invoices in {args.out}")


if __name__ == "__main__":
    main()