# Invoice Pipeline

An end-to-end pipeline that reads invoices in English, Swedish and Finnish:
synthetic data generation, OCR, and field extraction (supplier, invoice number,
date, VAT, total). Document classification and an API are planned.

This is my own project, built to learn document automation for accounting.

**Status:** work in progress. Data generation, OCR evaluation, preprocessing and
field extraction on clean pages are done. All results so far are on synthetic
invoices.

## What works so far

- **Data schema** (`src/schema.py`, `schema.md`): one validated record per
  document (supplier, invoice number, date, currency, total, VAT).
- **Synthetic invoice generator**: PDF invoices in English, Swedish and Finnish
  with local formats (decimal comma, date styles, VAT labels such as *moms* and
  *ALV*), four page layouts, a JSON file with the correct answer and a TXT file
  with the printed text. An optional mode varies the label wording and the line
  order, and a held-out mode uses wordings never seen in development.
- **OCR reader**: PDF to image to text with Tesseract.
- **OCR evaluation**: accuracy per language and noise level (character error
  rate and per-field hit rate).
- **Noise simulation**: tilt, blur, lower resolution and grain, calibrated into
  four levels (clean, mild, heavy, severe).
- **Preprocessing**: grayscale, median filter and upscaling before OCR.
- **Field extraction**: keyword rules and a value-based extractor, evaluated on a
  development set and a held-out test set.
- **Tests**: automated tests for every module (`pytest`).

## Setup

Requires Python 3.12 and Tesseract OCR with the English, Finnish and Swedish
language data installed.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

Fonts: download DejaVu Sans (`DejaVuSans.ttf` and `DejaVuSans-Bold.ttf`) from
https://dejavu-fonts.github.io and place them in `assets/fonts/`.

Check that Tesseract sees the languages:

```bash
tesseract --list-langs     # should list eng, fin, swe
```

## Usage

Generate the synthetic dataset (100 invoices per language). This creates a PDF,
a JSON answer file and a TXT file with the printed text for each invoice:

```bash
python -m src.generate.build_dataset --count 100
```

Generate the varied datasets used for extraction (the second one uses held-out
label wordings for invoices 71 and up):

```bash
python -m src.generate.build_dataset --count 100 --varied --out data/synthetic_varied
python -m src.generate.build_dataset --count 100 --varied --holdout --out data/synthetic_holdout
```

Measure OCR accuracy:

```bash
python -m src.ocr.evaluate --limit 30
python -m src.ocr.evaluate --limit 30 --levels heavy severe --preprocess
```

Measure field extraction (development set, then the test set):

```bash
python -m src.extract.evaluate --extractor values
python -m src.extract.evaluate --extractor values --folder data/synthetic_holdout --split test
```

Run the tests:

```bash
python -m pytest -v
```

## OCR results (baseline, no preprocessing)

30 synthetic invoices per language, first page only. The accuracy range shows
the lowest and highest result among the five fields (supplier, invoice number,
date, VAT, total).

| Noise level | CER (en / sv / fi) | Field accuracy (en) | Field accuracy (sv) | Field accuracy (fi) |
|---|---|---|---|---|
| clean | 0.0000 / 0.0000 / 0.0000 | 100% | 100% | 100% |
| mild | 0.0000 / 0.0003 / 0.0003 | 100% | 100% | 96.7–100% |
| heavy | 0.0688 / 0.0175 / 0.0208 | 90.0–93.3% | 93.3–100% | 93.3–100% |
| severe | 0.4667 / 0.4009 / 0.4346 | 53.3% | 50.0–60.0% | 50.0–56.7% |

Full output: `results/ocr_baseline.txt`.

### How the noise levels were chosen

The levels were calibrated by testing each factor separately. Resolution loss
alone did not hurt Tesseract at this text size. Blur and tilt reduced accuracy
gradually. Strong random grain was the main problem: above a certain strength
Tesseract fails on a whole page rather than on single characters (this is why
all fields in the `severe` rows are almost equal).

## Preprocessing

Before OCR, each image is converted to grayscale, cleaned with a 3x3 median
filter (removes grain) and upscaled by 1.5 (from 200 to about 300 DPI). Same
30 invoices per language and the same damage as the baseline.

| Noise level | Language | CER before → after | Field accuracy before → after |
|---|---|---|---|
| heavy | en | 0.0688 → 0.0101 | 90.0–93.3% → 96.7–100% |
| heavy | sv | 0.0175 → 0.0173 | 93.3–100% → 93.3–100% |
| heavy | fi | 0.0208 → 0.0381 | 93.3–100% → 93.3–100% |
| severe | en | 0.4667 → 0.0109 | 53.3% → 86.7–100% |
| severe | sv | 0.4009 → 0.0355 | 50.0–60.0% → 86.7–100% |
| severe | fi | 0.4346 → 0.0026 | 50.0–56.7% → 86.7–100% |

The filter fixes the whole-page failures caused by strong grain. At moderate
noise (`heavy`) the effect is small and mixed: English improves, Swedish is
unchanged and Finnish CER is slightly worse (a difference of one or two pages,
within the noise of a 30-invoice sample).

Full output: `results/ocr_preprocessed.txt`.

## Field extraction

Two extractors read the OCR text and return the five fields. A field they cannot
find is returned as `None`, never as a guess, so such an invoice could be sent to
manual review.

- **Keyword rules** (`src/extract/rules.py`): a value follows a known label word
  such as `Total` or `Yhteensä`.
- **Value-based** (`src/extract/values.py`): ignores the label and uses what the
  value looks like. Two amounts: the larger is the total, the smaller is the VAT.
  One date. One number of three or more digits.

### Data split

Invoices 1-70 per language are the development set (used to design and debug).
Invoices 71-100 are the test set. In the test set the label wordings are ones
that appear nowhere in the development data and nowhere in the rules (for
example `Net payable`, `Kokonaissumma`, `Slutsumma`). The keyword rules were
frozen before the test set was run. The value-based extractor was run on the
test set before the development set and was not changed after seeing the result.
A unit test of the value-based extractor (`tests/test_values.py`) uses the
held-out wordings on generated text; the extractor was not modified because of it.

### Results (clean pages; 70 dev and 30 test invoices per language)

| Extractor | Dev, known labels | Test, unseen labels |
|---|---|---|
| Keyword rules | 100% on all fields | supplier 100%, other four fields 0% |
| Value-based | 100% on all fields | 100% on all fields |

Before the dev label words were added to the keyword rules, the same rules scored
14-60% per field on dev (supplier 100%, English VAT 100% by accident), roughly the
share of invoices that happened to use the one label they knew. All failures were
"not found" (`None`); none was a wrong value.

Full output: `results/extract_rules_dev_clean.txt`,
`results/extract_rules_dev_known_labels.txt`,
`results/extract_rules_test_unseen_labels.txt`,
`results/extract_values_dev.txt`,
`results/extract_values_test_unseen_labels.txt`.

What this shows: a keyword list only recognises words it was given, while a
value-based extractor does not depend on the wording. What it does not show: the
value-based result depends on the synthetic invoices having exactly one date, one
number and two amounts.

## Limitations

- All documents are **synthetic**: one font, one page, clean layout. Results show
  how the pipeline behaves under controlled changes, not how it performs on real
  scanned invoices.
- The noise is random grain added to every pixel, which is harsher for Tesseract
  than the noise of a real scanner or phone camera.
- With 30 invoices per language, one failed page changes a result by about 3
  percentage points, so small differences between languages are not meaningful.
- Invoices contain only five fields and no line items or tables.
- The median filter is well matched to this synthetic noise (independent per-pixel
  grain). Gains on real scans may be smaller.
- Preprocessing was chosen after seeing the baseline results and evaluated on the
  same invoices; no parameters were tuned.
- Synthetic invoices have exactly one date, one number and two amounts, which the
  value-based extractor relies on. Real invoices have line items, subtotals, due
  dates, phone numbers and bank details.
- Extraction was measured on clean pages only; OCR errors in digits would produce
  wrong values, not just missing ones.
- The held-out label wordings were written by me, so they are a test of unseen
  words, not of unseen invoice layouts.

## Roadmap

- [x] Data schema, synthetic generator, tests
- [x] OCR reader and evaluation with noise levels
- [x] Image preprocessing and before/after comparison
- [x] Field extraction: keyword rules and value-based, with a held-out test set
- [ ] Extraction under OCR noise (with and without preprocessing)
- [ ] Document type classifier (invoice, receipt, other)
- [ ] Evaluation on real receipts (SROIE)
- [ ] API (FastAPI), review dashboard, Docker

## Project structure

```
assets/fonts/            DejaVu Sans fonts used for the PDFs
data/synthetic*/         generated PDFs, JSON labels and TXT files (not committed)
results/                 saved evaluation output
src/generate/            synthetic data: truth, formatting, PDF, dataset builder
src/ocr/                 OCR reader, noise, preprocessing, evaluation
src/extract/             dev/test split, parsing, keyword rules, value-based extractor
src/schema.py            data schema
tests/                   automated tests
```