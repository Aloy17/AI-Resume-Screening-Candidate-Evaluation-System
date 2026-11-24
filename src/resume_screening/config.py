
"""Configuration: scoring weights and runtime settings."""

from __future__ import annotations

import os
import re
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
        values = [getattr(self, category) for category in CATEGORIES]

        if any(value < 0 for value in values):
            raise ValueError("Weights must be non-negative.")

        if abs(sum(values) - 1.0) > 1e-6:
            raise ValueError(
                f"Weights must sum to 1.0, got {sum(values):.4f}."
            )


def _normalize_profile_name(name: str) -> str:
    """Normalize a JD filename or profile name for matching."""

    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _build_weights(raw: dict, profile_name: str) -> Weights:
    if not isinstance(raw, dict):
        raise ValueError(
            f"Weight profile '{profile_name}' must be a YAML mapping."
        )

    unknown = set(raw) - set(CATEGORIES)

    if unknown:
        raise ValueError(
            f"Unknown weight categories in '{profile_name}': "
            f"{sorted(unknown)}"
        )

    return Weights(
        **{
            category: float(raw.get(category, getattr(Weights(), category)))
            for category in CATEGORIES
        }
    )


def load_weights(
    path: str | Path | None = None,
    jd_path: str | Path | None = None,
) -> Weights:
    """Load JD-specific weights, falling back to default weights."""

    config_path = Path(
        path or os.environ.get("WEIGHTS_FILE", DEFAULT_WEIGHTS_FILE)
    )

    if not config_path.exists():
        return Weights()

    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}

    if not isinstance(data, dict):
        raise ValueError("Weights configuration must be a YAML mapping.")

    # Backward compatibility with the original configuration format.
    if "weights" in data:
        return _build_weights(data["weights"], "weights")

    default_raw = data.get("default", {})
    default_weights = _build_weights(default_raw, "default")

    profiles = data.get("profiles", {})

    if not isinstance(profiles, dict):
        raise ValueError("'profiles' must be a YAML mapping.")

    if jd_path is None:
        return default_weights

    jd_name = _normalize_profile_name(Path(jd_path).stem)

    for profile_name, profile_weights in profiles.items():
        normalized_profile = _normalize_profile_name(profile_name)

        if normalized_profile == jd_name:
            return _build_weights(profile_weights, profile_name)

    return default_weights


def embedding_model_name() -> str:
    return os.environ.get("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)


def tesseract_cmd() -> str | None:
    return os.environ.get("TESSERACT_CMD") or None
