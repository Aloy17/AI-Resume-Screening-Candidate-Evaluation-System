
"""Stage 5a: Skills matching using exact and semantic similarity."""

from __future__ import annotations

import numpy as np

from ..embeddings.embedder import Embedder
from ..models import JobDescription, ResumeData


REQUIRED_WEIGHT = 0.80
PREFERRED_WEIGHT = 0.20

SEMANTIC_THRESHOLD = 0.75


def _normalize_skill(skill: str) -> str:
    """Normalize a skill name for exact comparison."""
    return " ".join(skill.lower().strip().split())


def _score_skill_group(
    candidate_skills: list[str],
    target_skills: list[str],
    embedder: Embedder,
) -> float:
    """Score one group of JD skills against candidate skills."""

    if not target_skills:
        return 0.0

    if not candidate_skills:
        return 0.0

    candidate_skills = sorted({
        _normalize_skill(skill)
        for skill in candidate_skills
        if skill.strip()
    })

    target_skills = sorted({
        _normalize_skill(skill)
        for skill in target_skills
        if skill.strip()
    })

    if not candidate_skills:
        return 0.0

    candidate_set = set(candidate_skills)

    # Exact matches receive full credit.
    unmatched_targets = [
        skill
        for skill in target_skills
        if skill not in candidate_set
    ]

    exact_matches = len(target_skills) - len(unmatched_targets)

    if not unmatched_targets:
        return 100.0

    # Compare remaining JD skills semantically.
    candidate_embeddings = embedder.embed(candidate_skills)
    target_embeddings = embedder.embed(unmatched_targets)

    similarities = np.matmul(
        target_embeddings,
        candidate_embeddings.T,
    )

    semantic_scores = []

    for row in similarities:
        best_similarity = float(np.max(row))

        if best_similarity >= SEMANTIC_THRESHOLD:
            semantic_scores.append(best_similarity)
        else:
            semantic_scores.append(0.0)

    total_score = exact_matches + sum(semantic_scores)

    return (total_score / len(target_skills)) * 100


def score_skills(
    resume: ResumeData,
    jd: JobDescription,
    embedder: Embedder,
) -> float:
    """Calculate the candidate's overall skills match score (0–100)."""

    required_skills = jd.required_skills
    preferred_skills = jd.preferred_skills

    if not required_skills and not preferred_skills:
        return 0.0

    candidate_skills = resume.skills

    required_score = _score_skill_group(
        candidate_skills,
        required_skills,
        embedder,
    )

    preferred_score = _score_skill_group(
        candidate_skills,
        preferred_skills,
        embedder,
    )

    if not preferred_skills:
        return round(required_score, 2)

    if not required_skills:
        return round(preferred_score, 2)

    final_score = (
        required_score * REQUIRED_WEIGHT
        + preferred_score * PREFERRED_WEIGHT
    )

    return round(final_score, 2)
