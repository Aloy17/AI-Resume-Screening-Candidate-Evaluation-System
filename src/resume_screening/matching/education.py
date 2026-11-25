
"""Stage 5c: Education matching against required and preferred qualifications."""

from __future__ import annotations

import re

from ..models import JobDescription, ResumeData


REQUIRED_WEIGHT = 0.80
PREFERRED_WEIGHT = 0.20

DEGREE_LEVELS = {
    "high school": 1,
    "secondary": 1,
    "ssc": 1,
    "hsc": 1,
    "diploma": 2,
    "associate": 2,
    "bachelor": 3,
    "undergraduate": 3,
    "bca": 3,
    "b tech": 3,
    "b e": 3,
    "b sc": 3,
    "b com": 3,
    "b a": 3,
    "bba": 3,
    "ba": 3,
    "master": 4,
    "postgraduate": 4,
    "mca": 4,
    "mba": 4,
    "m tech": 4,
    "m e": 4,
    "m sc": 4,
    "m com": 4,
    "ma": 4,
    "doctorate": 5,
    "phd": 5,
    "doctoral": 5,
}

FIELD_ALIASES = {
    "computer science": {"computer science", "cs"},
    "information technology": {"information technology", "it"},
    "computer applications": {
        "computer applications",
        "computer application",
        "mca",
        "bca",
    },
    "software engineering": {"software engineering"},
    "electronics": {"electronics", "ece"},
    "electrical engineering": {"electrical engineering", "eee"},
    "mechanical engineering": {"mechanical engineering"},
    "data science": {"data science"},
    "artificial intelligence": {"artificial intelligence", "ai"},
    "cybersecurity": {"cybersecurity", "cyber security"},
    "information security": {"information security"},
    "business administration": {
        "business administration",
        "management",
        "mba",
        "bba",
    },
}


def is_education_applicable(jd: JobDescription) -> bool:
    """Education is applicable only when the JD has a degree requirement."""

    return bool(jd.required_education or jd.preferred_education)


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


def _extract_field_requirement(requirement: str) -> str:
    """Remove degree-level terms and qualification filler words."""

    field = _normalize(requirement)

    for degree in sorted(DEGREE_LEVELS, key=len, reverse=True):
        field = re.sub(
            rf"\b{re.escape(degree)}\b",
            " ",
            field,
        )

    field = re.sub(
        r"\b(of|in|or|a|an|degree|equivalent|related|field|"
        r"minimum|preferred|required|and|technical|completed|"
        r"earned|obtained|graduated|hold|holder|held|must)\b",
        " ",
        field,
    )

    return " ".join(field.split())


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
    field_requirement = _extract_field_requirement(requirement)
    completion_required = bool(
        re.search(
            r"\b(completed|earned|obtained|graduated|hold|holder|held)\b",
            requirement,
            re.IGNORECASE,
        )
    )

    best_score = 0.0

    for entry in education_entries:
        candidate_degree = entry.degree or ""
        candidate_field = entry.field_of_study or ""
        in_progress = entry.in_progress or bool(
            re.search(
                r"\b(pursuing|in progress|currently enrolled|"
                r"currently studying|expected(?: graduation)?|present|current)\b",
                candidate_degree,
                re.IGNORECASE,
            )
        )

        candidate_text = " ".join(
            filter(
                None,
                [
                    candidate_degree,
                    candidate_field,
                    entry.institution,
                ],
            )
        )

        candidate_level = _degree_level(candidate_degree)

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

        if in_progress and required_level is not None:
            if completion_required:
                score = 0.0
            else:
                incomplete_level_score = (
                    max(0, required_level - 1) / required_level
                ) * 100
                score = min(score, incomplete_level_score)

        if field_requirement and required_level is not None:
            # Include the degree itself because parsers may not have
            # populated field_of_study separately.
            field_match = _field_score(
                f"{candidate_degree} {candidate_field}",
                field_requirement,
            )

            score *= 0.70 + 0.30 * field_match / 100

        best_score = max(best_score, score)

    return best_score


def score_education(
    resume: ResumeData,
    jd: JobDescription,
) -> float | None:
    """Calculate the candidate's education match score (0–100)."""

    required = jd.required_education
    preferred = jd.preferred_education

    if not required and not preferred:
        return None

    if not resume.education:
        return 0.0

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
