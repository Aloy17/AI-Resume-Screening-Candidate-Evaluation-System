"""Stage 2: Text extraction from PDF resumes (PyMuPDF, with Tesseract OCR fallback)."""

from __future__ import annotations

from pathlib import Path

MIN_CHARS_PER_PAGE = 50


def extract_text(pdf_path: str | Path) -> str:
    """Extract text from a PDF with PyMuPDF; fall back to OCR if the PDF looks scanned."""
    raise NotImplementedError


def is_scanned(text: str, page_count: int) -> bool:
    """Return True if the extracted text is too sparse to be a real text layer."""
    raise NotImplementedError


def ocr_extract(pdf_path: str | Path) -> str:
    """Render each page to an image and run Tesseract OCR on it."""
    raise NotImplementedError
