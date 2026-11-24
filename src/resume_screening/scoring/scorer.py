
"""Stage 6: Combine category scores into one suitability score."""

from __future__ import annotations

from ..config import Weights
from ..models import CategoryScores


def compute_final_score(
    scores: CategoryScores,
    weights: Weights,
) -> float:
    """Calculate the weighted suitability score (0–100)."""

    category_scores = {
        "skills": scores.skills,
        "experience": scores.experience,
        "education": scores.education,
        "projects": scores.projects,
    }

    for category, score in category_scores.items():
        if not 0.0 <= score <= 100.0:
            raise ValueError(
                f"{category} score must be between 0 and 100."
            )

    total_weight = (
        weights.skills
        + weights.experience
        + weights.education
        + weights.projects
    )

    if not 0.99 <= total_weight <= 1.01:
        raise ValueError(
            f"Category weights must sum to 1.0, got {total_weight}."
        )

    final_score = (
        scores.skills * weights.skills
        + scores.experience * weights.experience
        + scores.education * weights.education
        + scores.projects * weights.projects
    )

    return round(final_score, 2)
