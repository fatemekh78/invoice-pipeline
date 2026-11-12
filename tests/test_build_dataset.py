import json

from src.generate.build_dataset import build_dataset
from src.schema import InvoiceLabel


def test_build_dataset_creates_matching_pdf_and_json_pairs(tmp_path):
    created = build_dataset(tmp_path, count_per_language=2, base_seed=1)

    assert created == 6  # 3 languages x 2 invoices
    assert len(list(tmp_path.glob("*.pdf"))) == 6

    for json_file in tmp_path.glob("*.json"):
        data = json.loads(json_file.read_text(encoding="utf-8"))
        InvoiceLabel(**data)  # the saved answer must still match the schema
        assert json_file.with_suffix(".pdf").exists()