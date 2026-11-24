
from pathlib import Path

import pymupdf


def extract_text(pdf_path: str | Path) -> str:
    """
    Extract selectable text from a PDF resume.

    Scanned or image-based PDFs are not supported.
    """

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are supported.")

    extracted_pages = []

    try:
        with pymupdf.open(pdf_path) as document:
            for page in document:
                page_text = page.get_text("text")

                if page_text.strip():
                    extracted_pages.append(page_text)

    except Exception as error:
        raise RuntimeError(
            f"Could not read PDF: {pdf_path.name}"
        ) from error

    extracted_text = "\n".join(extracted_pages).strip()

    if not extracted_text:
        raise ValueError(
            f"No selectable text found in {pdf_path.name}. "
            "Scanned or image-based PDFs are not supported."
        )

    return extracted_text
