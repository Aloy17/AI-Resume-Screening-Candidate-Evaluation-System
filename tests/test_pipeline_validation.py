import pytest
from src.resume_screening.pipeline import validate_resume_text

def test_rejects_short_resume():
    with pytest.raises(ValueError): validate_resume_text("Short text")

def test_rejects_non_ats_resume():
    with pytest.raises(ValueError): validate_resume_text("This is a long enough document " * 10)

def test_accepts_resume_with_standard_sections():
    text="".join([f"{heading}\nSome meaningful resume content here.\n" for heading in ["Summary","Skills","Education"]])
    validate_resume_text(text)
