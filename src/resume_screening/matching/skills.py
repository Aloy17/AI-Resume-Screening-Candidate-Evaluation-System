
"""Stage 5a: Skills matching using exact and one-to-one semantic similarity."""

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
    """Score JD skills while allowing each candidate skill one match."""

    candidates = sorted({
        _normalize_skill(skill)
        for skill in candidate_skills
        if skill.strip()
    })
    targets = sorted({
        _normalize_skill(skill)
        for skill in target_skills
        if skill.strip()
    })

    if not targets or not candidates:
        return 0.0

    candidate_indices = {
        skill: index for index, skill in enumerate(candidates)
    }

    # Exact matches take priority and reserve their candidate skills.
    exact_matches = set(candidates) & set(targets)
    matched_targets = set(exact_matches)
    matched_candidates = {
        candidate_indices[skill] for skill in exact_matches
    }

    total_score = float(len(exact_matches))
    unmatched_targets = [
        skill for skill in targets if skill not in matched_targets
    ]
    available_candidates = [
        (index, skill)
        for index, skill in enumerate(candidates)
        if index not in matched_candidates
    ]

    if unmatched_targets and available_candidates:
        candidate_texts = [
            skill for _, skill in available_candidates
        ]

        candidate_embeddings = embedder.embed(candidate_texts)
        target_embeddings = embedder.embed(unmatched_targets)

        similarities = target_embeddings @ candidate_embeddings.T

        # Build all eligible pairs, then assign the strongest pairs first.
        pairs = []

        for target_index, row in enumerate(similarities):
            for candidate_index, similarity in enumerate(row):
                score = float(similarity)

                if score >= SEMANTIC_THRESHOLD:
                    pairs.append(
                        (
                            score,
                            target_index,
                            candidate_index,
                        )
                    )

        pairs.sort(reverse=True)

        assigned_targets = set()
        assigned_candidates = set()

        for score, target_index, candidate_index in pairs:
            if target_index in assigned_targets:
                continue

            if candidate_index in assigned_candidates:
                continue

            total_score += min(score, 1.0)
            assigned_targets.add(target_index)
            assigned_candidates.add(candidate_index)

    return (total_score / len(targets)) * 100


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
