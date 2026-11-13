import argparse
import json
import random
from pathlib import Path

from src.generate.formatting import format_invoice_text
from src.generate.pdf import LAYOUTS, render_invoice_pdf
from src.generate.truth import LANGUAGE_SETTINGS, make_invoice_truth
from src.schema import InvoiceLabel


def build_dataset(
    output_dir: Path, count_per_language: int, base_seed: int = 0, varied: bool = False
) -> int:
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

            # Drawn AFTER the truth and the layout, so the invoice data and the
            # layout are identical with and without --varied
            text = format_invoice_text(truth, rng) if varied else format_invoice_text(truth)

            render_invoice_pdf(text, output_dir / f"{doc_id}.pdf", layout)
            (output_dir / f"{doc_id}.txt").write_text(text, encoding="utf-8")

            label = InvoiceLabel(**truth).model_dump(mode="json")
            (output_dir / f"{doc_id}.json").write_text(
                json.dumps(label, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            created += 1

    return created


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic invoices (PDF + JSON + TXT).")
    parser.add_argument("--count", type=int, default=100, help="invoices per language")
    parser.add_argument("--out", default="data/synthetic", help="output folder")
    parser.add_argument("--varied", action="store_true",
                        help="use several label wordings and a random line order")
    args = parser.parse_args()

    total = build_dataset(Path(args.out), args.count, varied=args.varied)
    print(f"Created {total} invoices in {args.out}")


if __name__ == "__main__":
    main()