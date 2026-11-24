"""Stage 5d: Project descriptions vs JD responsibilities and requirements via cosine similarity. Returns 0 to 100."""

from __future__ import annotations

from ..embeddings import Embedder
from ..models import JobDescription, ResumeData


def score_projects(resume: ResumeData, jd: JobDescription, embedder: Embedder) -> float:
    raise NotImplementedError
