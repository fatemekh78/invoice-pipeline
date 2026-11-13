# invoice-pipeline

My own project, built from scratch.

**Goal:** a pipeline that reads invoices and receipts, works out what kind of document each one is, and pulls the key fields (vendor, date, total) out into structured data. It is built and tested on synthetic invoices whose correct answers are known, then evaluated on real scanned receipts from the SROIE dataset.

## Structure

```
invoice-pipeline/
├── data/
│   ├── synthetic/      # generated invoices (PDF + labels)
│   └── sroie/          # real receipts
├── src/
│   ├── generate/       # synthetic invoice generator
│   ├── ocr/
│   ├── classify/
│   └── extract/
├── tests/
└── README.md
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
```
## Generate the synthetic dataset

    python -m src.generate.build_dataset --count 100

Creates PDF invoices (English, Swedish, Finnish) with a matching JSON answer file for each, in `data/synthetic/`.


# Invoice Pipeline

An end-to-end pipeline that reads invoices in English, Swedish and Finnish:
synthetic data generation, OCR, and (in progress) document classification and
field extraction.

This is my own project, built to learn document automation for accounting.

**Status:** work in progress. Data generation and OCR evaluation are done.

## What works so far

- **Data schema** (`src/schema.py`, `schema.md`): one validated record per
  document (supplier, invoice number, date, currency, total, VAT).
- **Synthetic invoice generator**: creates PDF invoices in English, Swedish and
  Finnish with local formats (decimal comma, date styles, VAT labels such as
  *moms* and *ALV*), four different page layouts, and a JSON file with the
  correct answer for each invoice.
- **OCR reader**: PDF to image to text with Tesseract.
- **OCR evaluation**: measures accuracy per language and per noise level, using
  character error rate (CER) and per-field hit rate.
- **Noise simulation**: tilt, blur, lower resolution and grain, calibrated into
  four levels (clean, mild, heavy, severe).
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

Generate the synthetic dataset (100 invoices per language):

```bash
python -m src.generate.build_dataset --count 100
```

This creates a PDF and a matching JSON answer file for each invoice in
`data/synthetic/`.

Measure OCR accuracy:

```bash
python -m src.ocr.evaluate --limit 30
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

### Preprocessing (in progress)
### Preprocessing

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

## Limitations

- All documents are **synthetic**: one font, one page, clean layout. Results
  show how OCR behaves under controlled damage, not how it performs on real
  scanned invoices.
- The noise is random grain added to every pixel, which is harsher for
  Tesseract than the noise of a real scanner or phone camera.
- With 30 invoices per language, one failed page changes a result by about
  3 percentage points, so small differences between languages are not
  meaningful.
- Invoices contain only five fields and no line items or tables.
- The median filter is well matched to this synthetic noise (independent
  per-pixel grain). Gains on real scans may be smaller.
- Preprocessing was chosen after seeing the baseline results and evaluated on
  the same invoices; no parameters were tuned.

## Roadmap

- [x] Data schema, synthetic generator, tests
- [x] OCR reader and evaluation with noise levels
- [x] Image preprocessing and before/after comparison
- [ ] Document type classifier (invoice, receipt, other)
- [ ] Field extraction (rules first, then a trained model)
- [ ] API (FastAPI) and review dashboard, Docker

## Project structure

```
assets/fonts/      DejaVu Sans fonts used for the PDFs
data/synthetic/    generated PDFs and JSON labels (not committed)
results/           saved evaluation output
src/generate/      synthetic data: truth, formatting, PDF, dataset builder
src/ocr/           OCR reader, noise, preprocessing, evaluation
src/schema.py      data schema
tests/             automated tests
```