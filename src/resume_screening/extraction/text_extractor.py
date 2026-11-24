"""Text-only PDF extraction. Image-only/scanned PDFs are rejected; OCR is never invoked."""
from pathlib import Path
import pymupdf

MIN_PAGE_TEXT_CHARS = 20

def extract_text_from_pdf(pdf_path: str) -> str:
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are supported.")
    with pymupdf.open(path) as document:
        if document.needs_pass:
            raise ValueError("Password-protected PDFs are not supported.")
        if not document:
            raise ValueError("The PDF contains no pages.")
        pages = [page.get_text("text").strip() for page in document]
    nonempty = [page for page in pages if len(page) >= MIN_PAGE_TEXT_CHARS]
    if not nonempty:
        raise ValueError("This PDF appears to be scanned or image-only. Upload a text-based PDF; OCR is not supported.")
    if len(nonempty) / len(pages) < 0.5:
        raise ValueError("Too many PDF pages contain no selectable text. Scanned/image-only PDFs are not accepted.")
    text = "\n".join(nonempty).strip()
    if len(text) < 80:
        raise ValueError("The PDF contains too little selectable text to be a valid resume or job description.")
    return text
