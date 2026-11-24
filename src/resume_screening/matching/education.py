
"""Stage 5c: Education matching against required and preferred qualifications."""

from __future__ import annotations

import re

from ..models import JobDescription, ResumeData


REQUIRED_WEIGHT = 0.80
PREFERRED_WEIGHT = 0.20

DEGREE_LEVELS = {
    "high school": 1,
    "secondary": 1,
    "diploma": 2,
    "associate": 2,
    "bachelor": 3,
    "undergraduate": 3,
    "master": 4,
    "postgraduate": 4,
    "doctorate": 5,
    "phd": 5,
    "doctoral": 5,
}

FIELD_ALIASES = {
    "computer science": {"computer science", "cs"},
    "information technology": {"information technology", "it"},
    "computer applications": {"computer applications", "mca"},
    "software engineering": {"software engineering"},
    "electronics": {"electronics", "ece"},
    "electrical engineering": {"electrical engineering", "eee"},
    "mechanical engineering": {"mechanical engineering"},
    "data science": {"data science"},
    "artificial intelligence": {"artificial intelligence", "ai"},
    "cybersecurity": {"cybersecurity", "cyber security"},
}


def _normalize(text: str) -> str:
    """Normalize text for qualification comparison."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return " ".join(text.split())


def _degree_level(text: str) -> int | None:
    """Identify the highest degree level mentioned in a qualification."""

    normalized = _normalize(text)

    for degree, level in sorted(
        DEGREE_LEVELS.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    ):
        if re.search(rf"\b{re.escape(degree)}\b", normalized):
            return level

    # Common degree abbreviations.
    if re.search(r"\b(b\s*tech|b\s*e|b\s*sc|b\s*ca|b\s*com|b\s*a)\b", normalized):
        return 3

    if re.search(r"\b(m\s*tech|m\s*e|m\s*sc|m\s*ca|m\s*com|m\s*a)\b", normalized):
        return 4

    return None


def _field_score(candidate_text: str, requirement_text: str) -> float:
    """Compare fields of study using known aliases and normalized text."""

    candidate = _normalize(candidate_text)
    requirement = _normalize(requirement_text)

    if not requirement:
        return 100.0

    if not candidate:
        return 0.0

    if requirement in candidate or candidate in requirement:
        return 100.0

    for aliases in FIELD_ALIASES.values():
        candidate_matches = any(
            re.search(rf"\b{re.escape(alias)}\b", candidate)
            for alias in aliases
        )
        requirement_matches = any(
            re.search(rf"\b{re.escape(alias)}\b", requirement)
            for alias in aliases
        )

        if candidate_matches and requirement_matches:
            return 100.0

    return 0.0


def _score_qualification(
    education_entries,
    requirement: str,
) -> float:
    """Score candidate education against one qualification requirement."""

    if not requirement.strip():
        return 100.0

    if not education_entries:
        return 0.0

    required_level = _degree_level(requirement)

    best_score = 0.0

    for entry in education_entries:
        candidate_text = " ".join(
            filter(
                None,
                [
                    entry.degree,
                    entry.field_of_study,
                    entry.institution,
                ],
            )
        )

        candidate_level = _degree_level(entry.degree)

        if required_level is None:
            normalized_requirement = _normalize(requirement)
            normalized_candidate = _normalize(candidate_text)

            score = (
                100.0
                if normalized_requirement in normalized_candidate
                else 0.0
            )
        elif candidate_level is None:
            score = 0.0
        elif candidate_level >= required_level:
            score = 100.0
        else:
            score = (candidate_level / required_level) * 100

        # Check whether the qualification also specifies a field.
        field_requirement = requirement

        for degree in DEGREE_LEVELS:
            field_requirement = re.sub(
                rf"\b{re.escape(degree)}\b",
                "",
                field_requirement,
                flags=re.IGNORECASE,
            )

        field_requirement = re.sub(
            r"\b(of|in|or|a|an|degree|equivalent|related|field|minimum|preferred|required)\b",
            " ",
            field_requirement,
            flags=re.IGNORECASE,
        ).strip()

        if field_requirement and required_level is not None:
            field_match = _field_score(
                entry.field_of_study,
                field_requirement,
            )

            # A field mismatch reduces the score but does not erase
            # an otherwise valid degree-level match.
            score = score * (0.70 + 0.30 * field_match / 100)

        best_score = max(best_score, score)

    return best_score


def score_education(
    resume: ResumeData,
    jd: JobDescription,
) -> float:
    """Calculate the candidate's education match score (0–100)."""

    required = jd.required_education
    preferred = jd.preferred_education

    if not required and not preferred:
        return 100.0

    required_score = _score_qualification(
        resume.education,
        required,
    )

    if not preferred:
        return round(required_score, 2)

    preferred_score = _score_qualification(
        resume.education,
        preferred,
    )

    if not required:
        return round(preferred_score, 2)

    final_score = (
        required_score * REQUIRED_WEIGHT
        + preferred_score * PREFERRED_WEIGHT
    )

    return round(final_score, 2)
