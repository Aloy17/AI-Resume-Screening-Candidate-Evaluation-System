
"""Stage 5b: Experience matching using years and responsibility similarity."""

from __future__ import annotations

from ..embeddings.embedder import Embedder
from ..models import JobDescription, ResumeData


YEARS_WEIGHT = 0.70
RESPONSIBILITIES_WEIGHT = 0.30


def _resume_has_experience_section(resume: ResumeData) -> bool:
    status = resume.extraction_status.get("experience")
    if status:
        normalized = status.value if hasattr(status, "value") else str(status)
        if normalized == "missing":
            return False
        return normalized in {"empty", "ambiguous", "extracted"}
    return bool(resume.experience)


def is_experience_applicable(resume: ResumeData, jd: JobDescription) -> bool:
    """Experience applies from resume evidence or JD experience criteria."""

    if _resume_has_experience_section(resume):
        return True

    has_year_requirement = (
        jd.min_experience_years > 0.0
        or jd.max_experience_years is not None
    )
    has_responsibility_criteria = bool(
        [item for item in jd.responsibilities if item.strip()]
    )
    return has_year_requirement or has_responsibility_criteria


def _score_years(resume: ResumeData, jd: JobDescription) -> float:
    """Score candidate experience against the JD's experience range."""

    candidate_years = max(0.0, resume.total_experience_years)
    minimum = max(0.0, jd.min_experience_years)
    maximum = jd.max_experience_years

    if maximum is not None and maximum < minimum:
        raise ValueError(
            "Maximum experience cannot be lower than minimum experience."
        )

    if minimum == 0.0 and maximum is None:
        return 100.0

    if candidate_years < minimum:
        return round((candidate_years / minimum) * 100, 2)

    # Experience above the preferred range is not automatically penalized.
    return 100.0


def _score_responsibilities(
    resume: ResumeData,
    jd: JobDescription,
    embedder: Embedder,
) -> float | None:
    """Score responsibilities when both sides contain usable evidence."""

    candidate_responsibilities = [
        responsibility.strip()
        for entry in resume.experience
        for responsibility in entry.responsibilities
        if responsibility.strip()
    ]

    jd_responsibilities = [
        responsibility.strip()
        for responsibility in jd.responsibilities
        if responsibility.strip()
    ]

    # Missing extraction is unknown evidence, not a zero match.
    if not candidate_responsibilities or not jd_responsibilities:
        return None

    candidate_embeddings = embedder.embed(candidate_responsibilities)
    jd_embeddings = embedder.embed(jd_responsibilities)

    similarities = jd_embeddings @ candidate_embeddings.T

    # Assign each candidate responsibility at most once.
    pairs = []
    for jd_index, row in enumerate(similarities):
        for candidate_index, similarity in enumerate(row):
            pairs.append((float(similarity), jd_index, candidate_index))

    pairs.sort(reverse=True)
    matched_jd = set()
    matched_candidates = set()
    total = 0.0

    for similarity, jd_index, candidate_index in pairs:
        if jd_index in matched_jd or candidate_index in matched_candidates:
            continue
        matched_jd.add(jd_index)
        matched_candidates.add(candidate_index)
        total += max(0.0, min(1.0, similarity))

    score = (total / len(jd_responsibilities)) * 100
    return min(100.0, score)


def score_experience(
    resume: ResumeData,
    jd: JobDescription,
    embedder: Embedder,
) -> float | None:
    """Calculate the candidate's experience match score (0–100)."""

    if not _resume_has_experience_section(resume):
        has_year_requirement = (
            jd.min_experience_years > 0.0
            or jd.max_experience_years is not None
        )
        has_responsibility_criteria = bool(
            [item for item in jd.responsibilities if item.strip()]
        )
        return 0.0 if has_year_requirement or has_responsibility_criteria else None

    if not resume.experience:
        return 0.0

    has_year_requirement = (
        jd.min_experience_years > 0.0
        or jd.max_experience_years is not None
    )
    has_responsibility_criteria = bool(
        [item for item in jd.responsibilities if item.strip()]
    )

    if not has_year_requirement and not has_responsibility_criteria:
        entry_score = min(len(resume.experience) / 3.0, 1.0) * 50.0
        responsibility_count = sum(
            len(entry.responsibilities)
            for entry in resume.experience
        )
        responsibility_score = min(responsibility_count / 5.0, 1.0) * 30.0
        duration_score = min(resume.total_experience_years / 3.0, 1.0) * 20.0
        return round(entry_score + responsibility_score + duration_score, 2)

    years_score = _score_years(resume, jd)

    responsibility_score = _score_responsibilities(
        resume,
        jd,
        embedder,
    )

    if (
        jd.min_experience_years == 0.0
        and jd.max_experience_years is None
    ):
        if responsibility_score is None:
            return 0.0
        return round(responsibility_score, 2)

    if responsibility_score is None:
        return round(years_score, 2)

    final_score = (
        years_score * YEARS_WEIGHT
        + responsibility_score * RESPONSIBILITIES_WEIGHT
    )

    return round(final_score, 2)
