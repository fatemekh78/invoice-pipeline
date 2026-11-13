from pathlib import Path

DEV_MAX_NUMBER = 70  # invoices 1-70 per language = development, 71+ = test


def document_number(pdf_path: Path) -> int:
    # "fi_0071.pdf" -> 71
    return int(Path(pdf_path).stem.split("_")[1])


def list_documents(folder: Path, language: str, split: str) -> list[Path]:
    if split not in ("dev", "test"):
        raise ValueError(f"Unknown split: {split}")

    files = sorted(Path(folder).glob(f"{language}_*.pdf"))
    if split == "dev":
        return [f for f in files if document_number(f) <= DEV_MAX_NUMBER]
    return [f for f in files if document_number(f) > DEV_MAX_NUMBER]