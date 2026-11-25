
"""Stage 6: Combine category scores into one suitability score."""

from __future__ import annotations

from ..config import Weights
from ..models import CategoryScores, CategoryStatus


def compute_final_score(
    scores: CategoryScores,
    weights: Weights,
) -> float | None:
    """Calculate the weighted suitability score (0–100)."""

    category_scores = {
        "skills": scores.skills,
        "experience": scores.experience,
        "education": scores.education,
        "projects": scores.projects,
    }

    for category, score in category_scores.items():
        status = scores.applicability.get(
            category,
            CategoryStatus.APPLICABLE,
        )
        if status == CategoryStatus.NOT_APPLICABLE:
            continue
        if score is None:
            raise ValueError(
                f"{category} has an applicable status without a numeric score."
            )
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

    applicable_weights = {
        "skills": weights.skills,
        "experience": weights.experience,
        "education": weights.education,
        "projects": weights.projects,
    }

    applicable_weight_total = sum(
        weight
        for category, weight in applicable_weights.items()
        if scores.applicability.get(
            category,
            CategoryStatus.APPLICABLE,
        ) == CategoryStatus.APPLICABLE
    )

    if applicable_weight_total == 0.0:
        return None

    final_score = sum(
        category_scores[category]
        * (applicable_weights[category] / applicable_weight_total)
        for category in category_scores
        if scores.applicability.get(
            category,
            CategoryStatus.APPLICABLE,
        ) == CategoryStatus.APPLICABLE
    )

    return round(final_score, 2)
