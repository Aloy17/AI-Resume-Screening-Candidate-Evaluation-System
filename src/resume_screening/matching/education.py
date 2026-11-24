"""Stage 5c: Education match against the JD's required qualification. Returns 0 to 100."""

from __future__ import annotations

from ..models import JobDescription, ResumeData


def score_education(resume: ResumeData, jd: JobDescription) -> float:
    raise NotImplementedError
