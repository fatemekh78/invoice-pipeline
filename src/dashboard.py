import hashlib
import json
import tempfile
from pathlib import Path

import pymupdf
import streamlit as st

from src.generate.formatting import SUPPORTED_LANGUAGES
from src.pipeline import process_pdf
from src.review import (
    FIELD_LABELS,
    FIELD_ORDER,
    build_review_record,
    describe_reason,
    parse_corrections,
)

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB

st.set_page_config(page_title="Invoice review", layout="wide")


@st.cache_data(show_spinner="Reading the invoice...")
def run_pipeline(pdf_bytes: bytes, language: str) -> dict:
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "upload.pdf"
        path.write_bytes(pdf_bytes)
        return process_pdf(path, language)


@st.cache_data
def render_first_page(pdf_bytes: bytes) -> bytes:
    with pymupdf.open(stream=pdf_bytes, filetype="pdf") as document:
        return document[0].get_pixmap(dpi=100).tobytes("png")


st.title("Invoice review")
st.caption(
    "Check the values read from the invoice, correct them if needed, and download "
    "the reviewed record. Everything is processed on this computer."
)

language = st.selectbox("Language of the invoice", list(SUPPORTED_LANGUAGES))
upload = st.file_uploader("PDF invoice", type="pdf")

if upload is None:
    st.info("Upload a PDF invoice to start.")
    st.stop()

pdf_bytes = upload.getvalue()
if len(pdf_bytes) > MAX_UPLOAD_BYTES:
    st.error("The file is too large (limit 10 MB).")
    st.stop()
if not pdf_bytes.startswith(b"%PDF"):
    st.error("The file is not a PDF.")
    st.stop()

try:
    result = run_pipeline(pdf_bytes, language)
    page_image = render_first_page(pdf_bytes)
except Exception:
    st.error("Could not read this PDF.")
    st.stop()

# A new file or language gets fresh input boxes
digest = hashlib.sha1(pdf_bytes + language.encode()).hexdigest()[:10]

left, right = st.columns(2)

with left:
    st.image(page_image, caption="First page")

with right:
    if result["needs_review"]:
        st.warning("This invoice needs a human check:")
        for reason in result["review_reasons"]:
            st.write(f"- {describe_reason(reason)}")
    else:
        st.success("No automatic check found a problem. Please still compare with the invoice.")

    with st.form("review"):
        raw = {
            name: st.text_input(
                FIELD_LABELS[name],
                value=result["fields"][name] or "",
                key=f"{name}-{digest}",
            )
            for name in FIELD_ORDER
        }
        submitted = st.form_submit_button("Check and prepare the record")

    if submitted:
        corrected, errors = parse_corrections(raw)

        if errors:
            for error in errors:
                st.error(error)
        else:
            record = build_review_record(language, result["fields"], corrected)

            if record["remaining_review_reasons"]:
                st.warning("Some checks still fail:")
                for reason in record["remaining_review_reasons"]:
                    st.write(f"- {describe_reason(reason)}")
            else:
                st.success(
                    "No automatic check found a problem. This does not prove the "
                    "values are correct: the checks cannot see a one-cent error."
                )

            st.download_button(
                "Download the reviewed record (JSON)",
                data=json.dumps(record, indent=2, ensure_ascii=False),
                file_name="reviewed_invoice.json",
                mime="application/json",
            )