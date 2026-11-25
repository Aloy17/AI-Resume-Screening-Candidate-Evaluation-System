
"""Stage 5d: Project matching using semantic similarity and technology overlap."""

from __future__ import annotations

import numpy as np

from ..embeddings.embedder import Embedder
from ..models import JobDescription, ResumeData


DESCRIPTION_WEIGHT = 0.70
TECHNOLOGY_WEIGHT = 0.30
DESCRIPTION_SIMILARITY_THRESHOLD = 0.65


def is_projects_applicable(jd: JobDescription) -> bool:
    """Projects are always applicable."""

    return True


def _normalize(value: str) -> str:
    """Normalize text for exact comparison."""
    return " ".join(value.lower().strip().split())


def _score_descriptions(
    project_texts: list[str],
    requirements: list[str],
    embedder: Embedder,
) -> float:
    """Score explicit project requirements using one-to-one matching."""

    if not requirements or not project_texts:
        return 0.0

    project_embeddings = embedder.embed(project_texts)
    requirement_embeddings = embedder.embed(requirements)

    similarities = requirement_embeddings @ project_embeddings.T

    pairs = []

    for requirement_index, row in enumerate(similarities):
        for project_index, similarity in enumerate(row):
            score = max(0.0, min(1.0, float(similarity)))
            if score >= DESCRIPTION_SIMILARITY_THRESHOLD:
                pairs.append((score, requirement_index, project_index))

    pairs.sort(reverse=True)

    matched_requirements = set()
    matched_projects = set()
    total_score = 0.0

    for score, requirement_index, project_index in pairs:
        if requirement_index in matched_requirements:
            continue

        if project_index in matched_projects:
            continue

        matched_requirements.add(requirement_index)
        matched_projects.add(project_index)
        total_score += score

    # Unmatched requirements receive zero rather than disappearing
    # from the denominator.
    return (total_score / len(requirements)) * 100


def _score_technologies(
    resume: ResumeData,
    jd: JobDescription,
) -> float | None:
    """Measure exact overlap between project technologies and JD skills."""

    candidate_technologies = {
        _normalize(technology)
        for project in resume.projects
        for technology in project.technologies
        if technology.strip()
    }

    target_technologies = {
        _normalize(skill)
        for skill in jd.required_skills + jd.preferred_skills
        if skill.strip()
    }

    # Missing extracted technology data is unknown, not a zero match.
    if not candidate_technologies or not target_technologies:
        return None

    matched = candidate_technologies & target_technologies

    return (len(matched) / len(target_technologies)) * 100


def score_projects(
    resume: ResumeData,
    jd: JobDescription,
    embedder: Embedder,
) -> float | None:
    """Calculate the candidate's project match score (0–100)."""

    if not is_projects_applicable(jd):
        return None

    if not resume.projects:
        return 0.0

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
        ).strip()
        for project in resume.projects
    ]

    project_texts = [
        text for text in project_texts if text
    ]

    if not jd.project_requirements:
        relevance_texts = [
            " ".join(
                filter(None, [project.name, project.description])
            ).strip()
            for project in resume.projects
        ]
        relevance_texts = [text for text in relevance_texts if text]

        criteria = []
        jd_skills = sorted(set(jd.required_skills + jd.preferred_skills))
        if jd_skills:
            criteria.append("Skills: " + ", ".join(jd_skills))
        criteria.extend(
            responsibility.strip()
            for responsibility in jd.responsibilities
            if responsibility.strip()
        )
        if not criteria:
            return 0.0

        jd_context = "Job requirements: " + " ".join(criteria)
        return round(
            _score_descriptions(
                relevance_texts,
                [jd_context],
                embedder,
            ),
            2,
        )

    description_score = None

    # Only explicit project requirements are valid description targets.
    if jd.project_requirements and project_texts:
        description_score = _score_descriptions(
            project_texts,
            jd.project_requirements,
            embedder,
        )

    technology_score = _score_technologies(resume, jd)

    available_components = []

    if description_score is not None:
        available_components.append(
            (description_score, DESCRIPTION_WEIGHT)
        )

    if technology_score is not None:
        available_components.append(
            (technology_score, TECHNOLOGY_WEIGHT)
        )

    if not available_components:
        return 0.0

    total_weight = sum(
        weight for _, weight in available_components
    )

    final_score = sum(
        score * weight
        for score, weight in available_components
    ) / total_weight

    return round(final_score, 2)
