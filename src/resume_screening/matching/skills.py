"""Stage 5a: Skills match, including variations and related terminology. Returns 0 to 100."""

from __future__ import annotations

from ..embeddings import Embedder
from ..models import JobDescription, ResumeData


def score_skills(resume: ResumeData, jd: JobDescription, embedder: Embedder) -> float:
    raise NotImplementedError
