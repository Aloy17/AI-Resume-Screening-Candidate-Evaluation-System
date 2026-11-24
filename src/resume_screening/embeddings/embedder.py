
from __future__ import annotations

import numpy as np
from sentence_transformers import SentenceTransformer

from ..config import embedding_model_name
from ..models import ResumeData


class Embedder:
    """Generate embeddings for resume and job description data."""

    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or embedding_model_name()
        self._model: SentenceTransformer | None = None

    def _load_model(self) -> SentenceTransformer:
        """Load the embedding model once, when first needed."""

        if self._model is None:
            self._model = SentenceTransformer(self.model_name)

        return self._model

    def embed(self, texts: list[str]) -> np.ndarray:
        """Convert a list of strings into normalized embeddings."""

        if not isinstance(texts, list):
            raise TypeError("Input must be a list of strings.")

        if not all(isinstance(text, str) for text in texts):
            raise TypeError("Every item must be a string.")

        if not texts:
            return np.empty((0, 0), dtype=np.float32)

        if any(not text.strip() for text in texts):
            raise ValueError("Input texts must not be empty.")

        model = self._load_model()

        embeddings = model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        return np.asarray(embeddings, dtype=np.float32)

    @staticmethod
    def _join_text(values: list[str]) -> str:
        """Combine non-empty text values into one string."""

        return " ".join(
            value.strip()
            for value in values
            if isinstance(value, str) and value.strip()
        )

    def embed_resume_sections(
        self,
        resume: ResumeData,
    ) -> dict[str, np.ndarray]:
        """Generate separate embeddings for each resume section.

        Empty sections receive zero vectors so all four categories
        have consistent embedding dimensions.
        """

        model = self._load_model()
        dimension = model.get_embedding_dimension()

        if dimension is None:
            raise RuntimeError(
                "Could not determine embedding dimensions."
            )

        section_texts = {
            "skills": self._join_text(resume.skills),

            "experience": self._join_text([
                self._join_text([
                    entry.title,
                    entry.company,
                    self._join_text(entry.responsibilities),
                ])
                for entry in resume.experience
            ]),

            "education": self._join_text([
                self._join_text([
                    entry.degree,
                    entry.field_of_study,
                    entry.institution,
                    str(entry.year) if entry.year else "",
                ])
                for entry in resume.education
            ]),

            "projects": self._join_text([
                self._join_text([
                    entry.name,
                    entry.description,
                    self._join_text(entry.technologies),
                ])
                for entry in resume.projects
            ]),
        }

        embeddings = {}

        for section, text in section_texts.items():
            if text:
                embeddings[section] = self.embed([text])[0]
            else:
                embeddings[section] = np.zeros(
                    dimension,
                    dtype=np.float32,
                )

        return embeddings


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors."""

    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)

    if a.shape != b.shape:
        raise ValueError(
            "Both vectors must have the same dimensions."
        )

    if a.ndim != 1:
        raise ValueError("Both inputs must be one-dimensional vectors.")

    denominator = float(np.linalg.norm(a) * np.linalg.norm(b))

    if denominator == 0.0:
        return 0.0

    return float(np.dot(a, b) / denominator)
