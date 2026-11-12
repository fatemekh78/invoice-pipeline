from src.generate.build_dataset import build_dataset
from src.ocr.evaluate import FIELD_NAMES, evaluate_language


def test_evaluate_language_returns_sensible_numbers(tmp_path):
    build_dataset(tmp_path, count_per_language=2, base_seed=1)

    result = evaluate_language(tmp_path, "fi", limit=2)

    assert result["documents"] == 2
    assert 0.0 <= result["cer"] <= 1.0
    assert set(result["field_hit_rate"]) == set(FIELD_NAMES)