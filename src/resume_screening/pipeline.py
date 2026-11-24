
"""End-to-end pipeline: PDF resumes + PDF job description in, ranked candidates out."""

from __future__ import annotations

from pathlib import Path

from .config import Weights, load_weights
from .embeddings import Embedder
from .extraction import extract_text
from .matching import (
    score_education,
    score_experience,
    score_projects,
    score_skills,
)
from .models import CandidateResult, CategoryScores
from .parsing import clean_text, parse_job_description, parse_resume
from .ranking import rank_candidates
from .scoring import compute_final_score


def collect_resume_paths(resume_dir: str | Path) -> list[Path]:
    """Collect PDF resumes from the specified directory."""

    resume_dir = Path(resume_dir)

    if not resume_dir.exists():
        raise FileNotFoundError(
            f"Resume directory not found: {resume_dir}"
        )

    if not resume_dir.is_dir():
        raise NotADirectoryError(
            f"Expected a directory: {resume_dir}"
        )

    return sorted(resume_dir.glob("*.pdf"))


def run_pipeline(
    resume_dir: str | Path,
    jd_path: str | Path,
    weights: Weights | None = None,
    embedder: Embedder | None = None,
) -> list[CandidateResult]:
    """Process resumes, compare them with a JD and rank candidates."""

    resume_paths = collect_resume_paths(resume_dir)

    if not resume_paths:
        raise ValueError(
            f"No PDF resumes found in {resume_dir}"
        )

    jd_path = Path(jd_path)

    if not jd_path.exists():
        raise FileNotFoundError(
            f"Job description PDF not found: {jd_path}"
        )

    if jd_path.suffix.lower() != ".pdf":
        raise ValueError(
            "Job description must be a PDF file."
        )

    weights = weights or load_weights()
    embedder = embedder or Embedder()

    # Extract and parse the job description.
    jd_text = clean_text(extract_text(jd_path))
    jd = parse_job_description(jd_text)

    results: list[CandidateResult] = []

    for pdf_path in resume_paths:
        # Extract and parse the resume.
        resume_text = clean_text(extract_text(pdf_path))

        resume = parse_resume(
            resume_text,
            candidate_id=pdf_path.stem,
            source_file=pdf_path.name,
        )

        # Calculate individual category scores.
        scores = CategoryScores(
            skills=score_skills(resume, jd, embedder),
            experience=score_experience(resume, jd, embedder),
            education=score_education(resume, jd),
            projects=score_projects(resume, jd, embedder),
        )

        # Calculate the overall suitability score.
        final_score = compute_final_score(scores, weights)

        results.append(
            CandidateResult(
                candidate_id=resume.candidate_id,
                source_file=resume.source_file,
                scores=scores,
                final_score=final_score,
            )
        )

    # Sort candidates and assign ranks.
    return rank_candidates(results)
