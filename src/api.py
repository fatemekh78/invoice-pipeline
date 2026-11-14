import logging
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from src.generate.formatting import SUPPORTED_LANGUAGES
from src.pipeline import process_pdf

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB

logger = logging.getLogger(__name__)
app = FastAPI(title="Invoice Pipeline", version="0.1.0")


class ExtractResponse(BaseModel):
    language: str
    fields: dict[str, str | None]
    needs_review: bool
    review_reasons: list[str]


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/extract", response_model=ExtractResponse)
def extract(file: UploadFile = File(...), language: str = Form(...)) -> dict:
    if language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language: {language}. Use one of {list(SUPPORTED_LANGUAGES)}",
        )

    content = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large")
    if not content.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="The file is not a PDF")

    # The uploaded file name is never used; the file is saved under a fixed name
    with tempfile.TemporaryDirectory() as folder:
        pdf_path = Path(folder) / "upload.pdf"
        pdf_path.write_bytes(content)
        try:
            return process_pdf(pdf_path, language)
        except Exception as error:
            logger.exception("Could not process the PDF")
            raise HTTPException(status_code=422, detail="Could not read the PDF") from error