from pathlib import Path

import pytest

from src.extract.split import document_number, list_documents


def test_document_number_reads_the_number_from_the_file_name():
    assert document_number(Path("fi_0071.pdf")) == 71


def test_dev_and_test_do_not_overlap(tmp_path):
    for number in (1, 70, 71, 100):
        (tmp_path / f"fi_{number:04d}.pdf").touch()
    (tmp_path / "sv_0001.pdf").touch()  # other language, must be ignored

    dev = list_documents(tmp_path, "fi", "dev")
    test = list_documents(tmp_path, "fi", "test")

    assert [p.stem for p in dev] == ["fi_0001", "fi_0070"]
    assert [p.stem for p in test] == ["fi_0071", "fi_0100"]


def test_unknown_split_is_rejected(tmp_path):
    with pytest.raises(ValueError):
        list_documents(tmp_path, "fi", "validation")