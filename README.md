# Invoice Pipeline

An end-to-end pipeline that reads invoices in English, Swedish and Finnish:
synthetic data generation, OCR, field extraction (supplier, invoice number,
date, VAT, total), a review layer that flags doubtful results, an API and a
small review dashboard. A document classifier and Docker packaging are planned.

This is my own project, built to learn document automation for accounting.

**Status:** work in progress. Data generation, OCR evaluation, preprocessing,
field extraction, the review layer, the API and the review dashboard are done.
All results so far are on synthetic invoices. Docker packaging and a document
type classifier are planned.

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
- **Review layer**: merges the two extractors and flags doubtful invoices for
  manual review (missing field, extractors disagree, VAT inconsistent with total).
- **API** (`src/api.py`): FastAPI endpoint that takes a PDF and a language and
  returns the extracted fields with review reasons.
- **Review dashboard** (`src/dashboard.py`): Streamlit page that shows the
  invoice next to the extracted fields and review reasons, lets a person correct
  values, and exports the reviewed record with the original and corrected values.
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

Measure the review layer (two extractors plus checks) under OCR noise:

```bash
python -m src.extract.review_eval --levels heavy severe --preprocess
```

Run the API and open http://127.0.0.1:8000/docs:

```bash
python -m uvicorn src.api:app --reload --reload-dir src
```

`POST /extract` takes a PDF and a language (`en`, `sv` or `fi`) and returns the
five fields as text (money as `"1245.50"`), a `needs_review` flag and the list
of review reasons. A file that is not a PDF is rejected with 400, a file over
10 MB with 413, and a PDF that cannot be read with 422.

Run the review dashboard (upload a PDF, see the extracted fields next to the
page, correct them and download the reviewed record):

```bash
python -m streamlit run src/dashboard.py
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

The 100% on dev is expected: the keywords were taken from the same label
wordings the generator uses for the development invoices. The informative
number is the test column.

Full output: `results/extract_rules_dev_clean.txt`,
`results/extract_rules_dev_known_labels.txt`,
`results/extract_rules_test_unseen_labels.txt`,
`results/extract_values_dev.txt`,
`results/extract_values_test_unseen_labels.txt`.

What this shows: a keyword list only recognises words it was given, while a
value-based extractor does not depend on the wording. What it does not show: the
value-based result depends on the synthetic invoices having exactly one date, one
number and two amounts.

### Each extractor alone under OCR noise

Development set, preprocessing on, 30 invoices per language. In the `severe`
English set, the keyword rules returned a wrong total or VAT for 3 invoices and
the value-based extractor also for 3 (in one invoice it swapped the two
amounts, so both VAT and total were wrong). Neither flagged these invoices.
Supplier names also had errors in the other languages, mostly in letter case
(`sjö` instead of `Sjö`).

Full output: `results/extract_rules_dev_noisy_preprocessed.txt`,
`results/extract_values_dev_noisy_preprocessed.txt`.

## Review layer

The two extractors are combined and checked so that a doubtful invoice goes to
manual review instead of being booked with a wrong value.

- **Merge** (`src/extract/validate.py`): if both extractors give the same value,
  keep it. If only one finds a value, use it. If both find different values,
  return `None` and flag the invoice.
- **Checks**: a missing field; VAT larger than the total; VAT that does not
  match the expected rate for the language (exact match, zero tolerance).

### Results under OCR noise (preprocessing on, 30 invoices per language)

Counted per invoice. "Critical" means invoice number, date, VAT or total.

| Set | Noise | Invoices with a wrong critical value | Flagged | Silent |
|---|---|---|---|---|
| dev | heavy | 0 | 0 | 0 |
| dev | severe | 2 (en) | 2 | 0 |
| test | heavy | 2 (en 1, sv 1) | 1 | 1 |
| test | severe | 4 (en 2, sv 1, fi 1) | 4 | 0 |

No correct invoice was flagged in any run. Invoices with only missing fields are
always flagged. Without the review layer, each extractor alone left 3 invoices
with a wrong critical value unflagged on dev (severe, English); the layer
brought this to 0 on dev. This was not measured on the test set.

Full output: `results/review_dev_noisy_preprocessed.txt`,
`results/review_test_noisy_preprocessed.txt`.

### The one silent error

On the test set, invoice `en_0089` had its total read as `1474.9` instead of
`1474.91`. A one-cent error in the total cannot be detected from the VAT alone:
the VAT check is only sensitive to larger errors, while a one-cent error in the
VAT is detected. Both cases have a unit test (`tests/test_validate.py`). Detecting
the total error would need redundancy on the invoice (for example a separate net
amount or line items). The dashboard says this to the reviewer instead of
claiming the values are correct.

### Supplier name

The supplier name has no check. Supplier errors (on dev mostly letter-case
differences) pass unflagged and are counted separately in the "any field" columns.

## API and dashboard

Both call the same function (`src/pipeline.py`): OCR with preprocessing, the two
extractors, the merge and the checks.

- A wrong language does not produce wrong values: with an English invoice sent
  as Finnish, the date, VAT and total came back empty and the invoice was
  flagged (checked by hand and by a test).
- The API checks the file content (`%PDF`) instead of trusting the file name or
  content type, limits the size, and does not use the uploaded file name.
- The dashboard only accepts amounts with digits 0-9 and a dot, and real dates
  in `YYYY-MM-DD`, so a typo is rejected instead of being converted silently. The
  exported record keeps the original and the corrected value of every field.

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
- Each extractor alone was measured under OCR noise on the development set only;
  the combined review layer was measured on development and test (30 invoices per
  language), so results under noise rest on small counts.
- The held-out label wordings were written by me, so they are a test of unseen
  words, not of unseen invoice layouts.
- The review checks were designed after seeing the errors on the development
  set, so dev results for the review layer are optimistic.
- The VAT-rate check uses one fixed rate per language and zero tolerance. Real
  invoices can have several rates and different rounding.
- The language chosen for an invoice also sets the expected VAT rate, so an
  invoice whose language and VAT rate do not belong together always needs a
  manual check.
- A one-cent error in the total is not detected by the checks (see "The one
  silent error"). A passing review does not prove the values are correct.
- The review layer was run once on the test set; its one silent error was not
  fixed afterwards, to keep the test result honest.
- Counts are small (30 invoices per language; 6 invoices with a wrong critical
  value on test), so these numbers show what kinds of errors occur, not precise rates.
- The API takes the language from the caller and does not detect it.
- The API and the dashboard are local tools without login, storage or
  multi-user support. The dashboard was tried by hand; only its logic
  (`src/review.py`) has automated tests.

## Roadmap

- [x] Data schema, synthetic generator, tests
- [x] OCR reader and evaluation with noise levels
- [x] Image preprocessing and before/after comparison
- [x] Field extraction: keyword rules and value-based, with a held-out test set
- [x] Extraction under OCR noise (preprocessing on), with a review layer
- [x] API (FastAPI)
- [x] Review dashboard (Streamlit)
- [ ] Docker
- [ ] Document type classifier (invoice, receipt, other)
- [ ] Evaluation on real receipts (SROIE)

## Project structure

```
assets/fonts/            DejaVu Sans fonts used for the PDFs
data/synthetic*/         generated PDFs, JSON labels and TXT files (not committed)
results/                 saved evaluation output
src/generate/            synthetic data: truth, formatting, PDF, dataset builder
src/ocr/                 OCR reader, noise, preprocessing, evaluation
src/extract/             dev/test split, parsing, keyword rules, value-based extractor, review layer
src/pipeline.py          OCR, both extractors, merge and checks for one PDF
src/api.py               FastAPI endpoint
src/review.py            correction parsing and review record for the dashboard
src/dashboard.py         Streamlit review page
src/schema.py            data schema
tests/                   automated tests
```