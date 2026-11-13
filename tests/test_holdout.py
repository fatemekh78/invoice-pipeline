from src.generate.build_dataset import build_dataset


def test_holdout_changes_only_the_test_invoices(tmp_path):
    varied = tmp_path / "varied"
    holdout = tmp_path / "holdout"
    build_dataset(varied, count_per_language=72, base_seed=1, varied=True)
    build_dataset(holdout, count_per_language=72, base_seed=1, varied=True, holdout=True)

    for txt in varied.glob("*.txt"):
        number = int(txt.stem.split("_")[1])
        same_text = txt.read_text(encoding="utf-8") == (holdout / txt.name).read_text(encoding="utf-8")
        assert same_text == (number <= 70)  # dev unchanged, test changed

    for json_file in varied.glob("*.json"):
        assert json_file.read_text(encoding="utf-8") == (holdout / json_file.name).read_text(encoding="utf-8")

  