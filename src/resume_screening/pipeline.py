"""End to end pipeline: PDF resumes + JD in, ranked candidates out."""

from __future__ import annotations

from pathlib import Path

from .config import Weights, load_weights
from .embeddings import Embedder
from .extraction import extract_text
from .matching import score_education, score_experience, score_projects, score_skills
from .models import CandidateResult, CategoryScores
from .parsing import clean_text, parse_job_description, parse_resume
from .ranking import rank_candidates
from .scoring import compute_final_score


def collect_resume_paths(resume_dir: str | Path) -> list[Path]:
    return sorted(Path(resume_dir).glob("*.pdf"))


def run_pipeline(
    resume_dir: str | Path,
    jd_path: str | Path,
    weights: Weights | None = None,
    embedder: Embedder | None = None,
) -> list[CandidateResult]:
    weights = weights or load_weights()
    embedder = embedder or Embedder()
    jd = parse_job_description(Path(jd_path).read_text())

    results: list[CandidateResult] = []
    for pdf_path in collect_resume_paths(resume_dir):
        text = clean_text(extract_text(pdf_path))
        resume = parse_resume(text, candidate_id=pdf_path.stem, source_file=pdf_path.name)
        scores = CategoryScores(
            skills=score_skills(resume, jd, embedder),
            experience=score_experience(resume, jd, embedder),
            education=score_education(resume, jd),
            projects=score_projects(resume, jd, embedder),
        )
        results.append(
            CandidateResult(
                candidate_id=resume.candidate_id,
                source_file=resume.source_file,
                scores=scores,
                final_score=compute_final_score(scores, weights),
            )
        )
    return rank_candidates(results)
