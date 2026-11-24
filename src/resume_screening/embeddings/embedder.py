"""Stage 4: Section level embeddings with a pretrained Sentence Transformer (all-MiniLM-L6-v2)."""

from __future__ import annotations

import numpy as np

from ..config import embedding_model_name
from ..models import ResumeData


class Embedder:
    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or embedding_model_name()
        self._model = None

    def embed(self, texts: list[str]) -> np.ndarray:
        """Return one vector per input text. Load the model lazily on first use."""
        raise NotImplementedError

    def embed_resume_sections(self, resume: ResumeData) -> dict[str, np.ndarray]:
        """Separate embeddings for skills, experience descriptions and projects, not one per resume."""
        raise NotImplementedError


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity of two 1D vectors, 0.0 if either has zero norm."""
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0.0:
        return 0.0
    return float(np.dot(a, b) / denom)
