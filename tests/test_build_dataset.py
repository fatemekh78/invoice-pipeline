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

def test_dataset_also_saves_the_printed_text(tmp_path):
    build_dataset(tmp_path, count_per_language=1, base_seed=1)

    assert len(list(tmp_path.glob("*.txt"))) == 3


def test_varied_dataset_changes_the_text_but_not_the_answers(tmp_path):
    plain = tmp_path / "plain"
    varied = tmp_path / "varied"
    build_dataset(plain, count_per_language=3, base_seed=1)
    build_dataset(varied, count_per_language=3, base_seed=1, varied=True)

    for json_file in varied.glob("*.json"):
        same = (plain / json_file.name).read_text(encoding="utf-8")
        assert json_file.read_text(encoding="utf-8") == same

    assert any(
        (plain / txt.name).read_text(encoding="utf-8") != txt.read_text(encoding="utf-8")
        for txt in varied.glob("*.txt")
    )