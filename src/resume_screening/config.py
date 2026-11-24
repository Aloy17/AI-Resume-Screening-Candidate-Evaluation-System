"""Configuration: scoring weights and runtime settings."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml

DEFAULT_WEIGHTS_FILE = Path("config/weights.yaml")
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CATEGORIES = ("skills", "experience", "education", "projects")


@dataclass(frozen=True)
class Weights:
    skills: float = 0.40
    experience: float = 0.25
    education: float = 0.15
    projects: float = 0.20

    def __post_init__(self) -> None:
        values = [getattr(self, c) for c in CATEGORIES]
        if any(v < 0 for v in values):
            raise ValueError("Weights must be non negative")
        if abs(sum(values) - 1.0) > 1e-6:
            raise ValueError(f"Weights must sum to 1.0, got {sum(values):.4f}")


def load_weights(path: str | Path | None = None) -> Weights:
    """Load weights from a YAML file, falling back to the defaults if no file is given or found."""
    path = Path(path or os.environ.get("WEIGHTS_FILE", DEFAULT_WEIGHTS_FILE))
    if not path.exists():
        return Weights()
    data = yaml.safe_load(path.read_text()) or {}
    raw = data.get("weights", {})
    unknown = set(raw) - set(CATEGORIES)
    if unknown:
        raise ValueError(f"Unknown weight categories: {sorted(unknown)}")
    return Weights(**{c: float(raw[c]) for c in CATEGORIES if c in raw})


def embedding_model_name() -> str:
    return os.environ.get("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)


def tesseract_cmd() -> str | None:
    return os.environ.get("TESSERACT_CMD") or None
