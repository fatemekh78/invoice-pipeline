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