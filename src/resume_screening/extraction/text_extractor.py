
from pathlib import Path
import pymupdf


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from all pages of a PDF resume.

    Args:
        pdf_path: Path to the candidate's PDF resume.

    Returns:
        Extracted text as a single string.
    """

    pdf_path = Path(pdf_path)

    # Check if the file exists
    if not pdf_path.exists():
        raise FileNotFoundError(
            f"Resume file not found: {pdf_path}"
        )

    # Validate PDF extension
    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are supported.")

    extracted_pages = []

    # Open the PDF
    with pymupdf.open(pdf_path) as document:

        if document.needs_pass:
            raise ValueError(
                "Password-protected PDFs are not supported."
            )

        # Extract text from every page
        for page in document:
            page_text = page.get_text("text")

            if page_text.strip():
                extracted_pages.append(page_text)

    # Combine extracted text
    full_text = "\n".join(extracted_pages)

    return full_text
