
"""Generate and cache embeddings for resume and job description data."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

from ..config import embedding_model_name
from ..models import ResumeData


DEFAULT_CACHE_PATH = Path("data/outputs/embedding_cache.json")
CACHE_VERSION = 1


class Embedder:
    """Generate embeddings and reuse previously cached vectors."""

    def __init__(
        self,
        model_name: str | None = None,
        cache_path: str | Path | None = None,
    ) -> None:
        self.model_name = model_name or embedding_model_name()
        self.cache_path = Path(cache_path or DEFAULT_CACHE_PATH)
        self._model: SentenceTransformer | None = None
        self._cache: dict[str, list[float]] = {}
        self._load_cache()

    def _load_model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def _cache_key(self, text: str) -> str:
        """Create a model-specific key for an input text."""

        content = f"{self.model_name}\0{text}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _load_cache(self) -> None:
        """Load cached embeddings when the cache exists."""

        if not self.cache_path.exists():
            return

        try:
            data = json.loads(
                self.cache_path.read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeError(
                f"Could not read embedding cache: {self.cache_path}"
            ) from error

        if data.get("version") != CACHE_VERSION:
            return

        if data.get("model_name") != self.model_name:
            return

        embeddings = data.get("embeddings", {})

        if not isinstance(embeddings, dict):
            raise ValueError("Embedding cache has an invalid format.")

        for key, vector in embeddings.items():
            if (
                isinstance(key, str)
                and isinstance(vector, list)
                and all(
                    isinstance(value, (int, float))
                    and np.isfinite(value)
                    for value in vector
                )
            ):
                self._cache[key] = vector

    def _save_cache(self) -> None:
        """Persist cached embeddings to disk."""

        self.cache_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        data = {
            "version": CACHE_VERSION,
            "model_name": self.model_name,
            "embeddings": self._cache,
        }

        temporary_path = self.cache_path.with_suffix(
            self.cache_path.suffix + ".tmp"
        )

        temporary_path.write_text(
            json.dumps(data, ensure_ascii=False),
            encoding="utf-8",
        )
        temporary_path.replace(self.cache_path)

    def embed(self, texts: list[str]) -> np.ndarray:
        """Return normalized embeddings, using the cache when possible."""

        if not isinstance(texts, list):
            raise TypeError("Input must be a list of strings.")

        if not all(isinstance(text, str) for text in texts):
            raise TypeError("Every item must be a string.")

        if not texts:
            return np.empty((0, 0), dtype=np.float32)

        if any(not text.strip() for text in texts):
            raise ValueError("Input texts must not be empty.")

        keys = [self._cache_key(text) for text in texts]

        missing_texts: dict[str, str] = {}

        for key, text in zip(keys, texts):
            if key not in self._cache:
                missing_texts[key] = text

        if missing_texts:
            model = self._load_model()

            new_embeddings = model.encode(
                list(missing_texts.values()),
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )

            for key, vector in zip(
                missing_texts.keys(),
                new_embeddings,
            ):
                self._cache[key] = np.asarray(
                    vector,
                    dtype=np.float32,
                ).tolist()

            self._save_cache()

        return np.asarray(
            [self._cache[key] for key in keys],
            dtype=np.float32,
        )

    @staticmethod
    def _join_text(values: list[str]) -> str:
        return " ".join(
            value.strip()
            for value in values
            if isinstance(value, str) and value.strip()
        )

    def embed_resume_sections(
        self,
        resume: ResumeData,
    ) -> dict[str, np.ndarray]:
        """Generate or retrieve embeddings for resume sections."""

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
        raise ValueError(
            "Both inputs must be one-dimensional vectors."
        )

    denominator = float(
        np.linalg.norm(a) * np.linalg.norm(b)
    )

    if denominator == 0.0:
        return 0.0

    return float(np.dot(a, b) / denominator)
