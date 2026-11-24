
"""Stage 5b: Experience matching using years and responsibility similarity."""

from __future__ import annotations

from ..embeddings.embedder import Embedder
from ..models import JobDescription, ResumeData


YEARS_WEIGHT = 0.70
RESPONSIBILITIES_WEIGHT = 0.30


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
    best_matches = similarities.max(axis=1)

    score = max(0.0, float(best_matches.mean())) * 100

    return min(100.0, score)


def score_experience(
    resume: ResumeData,
    jd: JobDescription,
    embedder: Embedder,
) -> float:
    """Calculate the candidate's experience match score (0–100)."""

    years_score = _score_years(resume, jd)

    responsibility_score = _score_responsibilities(
        resume,
        jd,
        embedder,
    )

    if responsibility_score is None:
        return round(years_score, 2)

    final_score = (
        years_score * YEARS_WEIGHT
        + responsibility_score * RESPONSIBILITIES_WEIGHT
    )

    return round(final_score, 2)
