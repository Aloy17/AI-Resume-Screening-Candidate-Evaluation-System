"""Stage 6: Combine category scores into one suitability score using predefined weights."""

from __future__ import annotations

from ..config import Weights
from ..models import CategoryScores


def compute_final_score(scores: CategoryScores, weights: Weights) -> float:
    """Weighted sum of the category scores, on a 0 to 100 scale."""
    return (
        scores.skills * weights.skills
        + scores.experience * weights.experience
        + scores.education * weights.education
        + scores.projects * weights.projects
    )
