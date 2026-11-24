"""Stage 5b: Experience match. Numeric rules on years plus responsibility similarity. Returns 0 to 100."""

from __future__ import annotations

from ..embeddings import Embedder
from ..models import JobDescription, ResumeData


def score_experience(resume: ResumeData, jd: JobDescription, embedder: Embedder) -> float:
    raise NotImplementedError
