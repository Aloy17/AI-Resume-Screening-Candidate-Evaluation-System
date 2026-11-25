
import re
import unicodedata


def clean_text(raw_text: str) -> str:
    """Clean extracted resume text while preserving its structure."""

    if not isinstance(raw_text, str):
        raise TypeError("Input must be a string.")

    if not raw_text.strip():
        raise ValueError("Cannot clean empty resume text.")

    text = unicodedata.normalize("NFC", raw_text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Rejoin words split by a hyphen at a PDF line break.
    # Example: "real-\ntime" becomes "real-time".
    text = re.sub(
        r"(?<=\w)-[ \t]*\n[ \t]*(?=\w)",
        "-",
        text,
    )

    # PDF generators commonly insert a few known invisible formatting
    # characters. Remove only those that interfere with text/heading parsing;
    # do not strip all Unicode format characters or meaningful script data.
    text = re.sub(r"[\u200b\u2060\ufeff]", "", text)

    text = "".join(
        char
        for char in text
        if char in "\n\t" or unicodedata.category(char) != "Cc"
    )

    cleaned_lines = []

    for line in text.split("\n"):
        line = re.sub(r"[ \t]+", " ", line)
        cleaned_lines.append(line.strip())

    text = "\n".join(cleaned_lines)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()
