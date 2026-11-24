
import re
import unicodedata


def clean_resume_text(text: str) -> str:
    """
    Clean and normalize extracted resume text.

    Args:
        text: Raw text extracted from a resume.

    Returns:
        Cleaned resume text.
    """

    if not isinstance(text, str):
        raise TypeError("Input must be a string.")

    if not text.strip():
        return ""

    # Normalize Unicode characters
    text = unicodedata.normalize("NFKC", text)

    # Remove invisible formatting characters
    text = "".join(
        char for char in text
        if unicodedata.category(char) != "Cf"
    )

    # Normalize bullet characters
    text = re.sub(r"[●•▪◦■◆]", "\n• ", text)

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Replace tabs with spaces
    text = text.replace("\t", " ")

    # Remove excessive spaces
    text = re.sub(r"[ ]{2,}", " ", text)

    # Clean individual lines
    lines = [line.strip() for line in text.split("\n")]

    # Remove unnecessary blank lines
    cleaned_lines = [line for line in lines if line]

    # Combine cleaned lines
    cleaned_text = "\n".join(cleaned_lines)

    return cleaned_text.strip()
