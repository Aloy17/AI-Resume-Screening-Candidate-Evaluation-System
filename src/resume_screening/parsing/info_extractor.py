"""Stage 3b: Turn cleaned text into structured data (skills, experience, education, projects)."""

from __future__ import annotations

from ..models import JobDescription, ResumeData


def parse_resume(clean_text: str, candidate_id: str, source_file: str = "") -> ResumeData:
    """Identify skills, work experience, education, projects and past roles and responsibilities."""
    raise NotImplementedError


def parse_job_description(text: str) -> JobDescription:
    """Extract required skills, minimum experience, required education and responsibilities from a JD."""
    raise NotImplementedError
