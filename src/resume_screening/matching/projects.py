
"""Stage 5d: Project matching using semantic similarity and technology overlap."""

from __future__ import annotations

import numpy as np

from ..embeddings.embedder import Embedder
from ..models import JobDescription, ResumeData


DESCRIPTION_WEIGHT = 0.70
TECHNOLOGY_WEIGHT = 0.30


def _normalize(value: str) -> str:
    """Normalize text for exact comparison."""
    return " ".join(value.lower().strip().split())


def _score_descriptions(
    project_texts: list[str],
    requirements: list[str],
    embedder: Embedder,
) -> float:
    """Score project descriptions against JD requirements."""

    if not requirements:
        return 0.0

    if not project_texts:
        return 0.0

    project_embeddings = embedder.embed(project_texts)
    requirement_embeddings = embedder.embed(requirements)

    similarities = requirement_embeddings @ project_embeddings.T

    # Each JD requirement is matched with the most relevant project.
    best_matches = similarities.max(axis=1)

    # Convert cosine similarity from [-1, 1] to [0, 100].
    normalized_scores = np.clip(best_matches, 0.0, 1.0)

    return float(normalized_scores.mean() * 100)


def _score_technologies(
    resume: ResumeData,
    jd: JobDescription,
) -> float:
    """Measure overlap between project technologies and JD skills."""

    candidate_technologies = {
        _normalize(technology)
        for project in resume.projects
        for technology in project.technologies
        if technology.strip()
    }

    required = {
        _normalize(skill)
        for skill in jd.required_skills
        if skill.strip()
    }

    preferred = {
        _normalize(skill)
        for skill in jd.preferred_skills
        if skill.strip()
    }

    target_technologies = required | preferred

    if not target_technologies:
        return 0.0

    matched = candidate_technologies & target_technologies

    return (len(matched) / len(target_technologies)) * 100


def score_projects(
    resume: ResumeData,
    jd: JobDescription,
    embedder: Embedder,
) -> float:
    """Calculate the candidate's project match score (0–100)."""

    if not resume.projects:
        return 0.0

    requirements = jd.project_requirements or jd.responsibilities

    project_texts = [
        " ".join(
            filter(
                None,
                [
                    project.name,
                    project.description,
                    " ".join(project.technologies),
                ],
            )
        )
        for project in resume.projects
    ]

    project_texts = [
        text.strip()
        for text in project_texts
        if text.strip()
    ]

    if not project_texts:
        return 0.0

    if not requirements:
        return 0.0

    description_score = _score_descriptions(
        project_texts,
        requirements,
        embedder,
    )

    technology_score = _score_technologies(resume, jd)

    final_score = (
        description_score * DESCRIPTION_WEIGHT
        + technology_score * TECHNOLOGY_WEIGHT
    )

    return round(final_score, 2)
