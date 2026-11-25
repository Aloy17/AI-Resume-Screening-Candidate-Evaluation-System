
"""Stage 5a: Skills matching using exact and one-to-one semantic similarity."""

from __future__ import annotations

import numpy as np

from ..embeddings.embedder import Embedder
from ..models import JobDescription, ResumeData


REQUIRED_WEIGHT = 0.80
PREFERRED_WEIGHT = 0.20
SEMANTIC_THRESHOLD = 0.75


def _resume_has_skills_section(resume: ResumeData) -> bool:
    status = resume.extraction_status.get("skills")
    if status:
        normalized = status.value if hasattr(status, "value") else str(status)
        if normalized == "missing":
            return False
        return normalized in {"empty", "ambiguous", "extracted"}
    return bool(resume.skills)


def is_skills_applicable(resume: ResumeData, jd: JobDescription) -> bool:
    """Skills require JD or resume evidence; neither means N/A."""

    has_resume_section = _resume_has_skills_section(resume)
    has_jd_requirements = bool(jd.required_skills or jd.preferred_skills)
    return has_resume_section or has_jd_requirements


def _normalize_skill(skill: str) -> str:
    """Normalize a skill name for exact comparison."""
    return " ".join(skill.lower().strip().split())


def _score_skill_group(
    candidate_skills: list[str],
    target_skills: list[str],
    embedder: Embedder,
    alternative_groups: list[list[str]] | None = None,
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

    target_set = set(targets)
    target_groups = []
    grouped_targets = set()

    for group in sorted(
        {
            tuple(sorted({
                _normalize_skill(skill)
                for skill in alternative_group
                if _normalize_skill(skill) in target_set
            }))
            for alternative_group in alternative_groups or []
        }
    ):
        if len(group) > 1 and not (set(group) & grouped_targets):
            target_groups.append(list(group))
            grouped_targets.update(group)

    target_groups.extend(
        [target] for target in targets if target not in grouped_targets
    )

    assigned_targets = set()
    assigned_candidates = set()
    total_score = 0.0

    # Exact matches take priority and reserve their candidate skills.
    exact_pairs = [
        (target_index, candidate_index)
        for target_index, group in enumerate(target_groups)
        for candidate_index, candidate in enumerate(candidates)
        if candidate in group
    ]
    for target_index, candidate_index in exact_pairs:
        if target_index in assigned_targets:
            continue
        if candidate_index in assigned_candidates:
            continue
        assigned_targets.add(target_index)
        assigned_candidates.add(candidate_index)
        total_score += 1.0

    unmatched_target_groups = [
        (index, group)
        for index, group in enumerate(target_groups)
        if index not in assigned_targets
    ]
    available_candidates = [
        (index, candidate)
        for index, candidate in enumerate(candidates)
        if index not in assigned_candidates
    ]

    if unmatched_target_groups and available_candidates:
        target_texts = sorted({
            skill
            for _, group in unmatched_target_groups
            for skill in group
        })
        target_embeddings = embedder.embed(target_texts)
        candidate_embeddings = embedder.embed(
            [candidate for _, candidate in available_candidates]
        )
        similarities = target_embeddings @ candidate_embeddings.T
        target_indices = {
            skill: index for index, skill in enumerate(target_texts)
        }

        pairs = []
        for group_index, group in unmatched_target_groups:
            member_indices = [target_indices[skill] for skill in group]
            group_similarities = similarities[member_indices].max(axis=0)
            for candidate_index, similarity in enumerate(group_similarities):
                score = float(similarity)
                if score >= SEMANTIC_THRESHOLD:
                    original_candidate_index = available_candidates[
                        candidate_index
                    ][0]
                    pairs.append(
                        (score, group_index, original_candidate_index)
                    )

        pairs.sort(reverse=True)
        for score, target_index, candidate_index in pairs:
            if target_index in assigned_targets:
                continue
            if candidate_index in assigned_candidates:
                continue
            assigned_targets.add(target_index)
            assigned_candidates.add(candidate_index)
            total_score += min(score, 1.0)

    return (total_score / len(target_groups)) * 100


def score_skills(
    resume: ResumeData,
    jd: JobDescription,
    embedder: Embedder,
) -> float | None:
    """Calculate the candidate's overall skills match score (0–100)."""

    required_skills = jd.required_skills
    preferred_skills = jd.preferred_skills

    if not required_skills and not preferred_skills:
        if not _resume_has_skills_section(resume):
            return None
        if not resume.skills:
            return 0.0

        unique_skills = sorted({
            _normalize_skill(skill)
            for skill in resume.skills
            if skill.strip()
        })
        return round(min(len(unique_skills) / 10.0, 1.0) * 100, 2)

    if not _resume_has_skills_section(resume):
        return 0.0

    candidate_skills = resume.skills

    required_score = _score_skill_group(
        candidate_skills,
        required_skills,
        embedder,
        jd.required_skill_alternatives,
    )

    preferred_score = _score_skill_group(
        candidate_skills,
        preferred_skills,
        embedder,
        jd.preferred_skill_alternatives,
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
