
import re
from typing import Any

import numpy as np

from src.resume_screening.embeddings.embedder import generate_embeddings


# =========================================================
# SEMANTIC MATCHING CONFIGURATION
# =========================================================

WEAK_SIMILARITY_LIMIT = 0.25
STRONG_SIMILARITY_LIMIT = 0.40
RELEVANCE_THRESHOLD = WEAK_SIMILARITY_LIMIT

TOP_K_EVIDENCE = 3


# =========================================================
# 1. TEXT CLEANING
# =========================================================

def clean_text(value: Any) -> str:

    if value is None:
        return ""

    if isinstance(value, list):
        value = " ".join(str(item) for item in value if item)

    if not isinstance(value, str):
        value = str(value)

    return re.sub(r"\s+", " ", value).strip()


def clean_text_list(value: Any) -> list[str]:

    if not value:
        return []

    if isinstance(value, str):
        value = [value]

    if not isinstance(value, list):
        return []

    return [
        clean_text(item)
        for item in value
        if clean_text(item)
    ]


# =========================================================
# 2. SIMILARITY CLASSIFICATION
# =========================================================

def classify_similarity(similarity: float) -> str:

    if similarity >= STRONG_SIMILARITY_LIMIT:
        return "strong"

    if similarity >= WEAK_SIMILARITY_LIMIT:
        return "moderate"

    return "weak"


# =========================================================
# 3. TEXT CHUNKING
# =========================================================

def split_into_chunks(text: str) -> list[str]:

    text = clean_text(text)

    if not text:
        return []

    sentences = re.split(r"(?<=[.!?])\s+", text)

    return [
        sentence.strip()
        for sentence in sentences
        if len(sentence.strip()) > 15
    ]


# =========================================================
# 4. JOB DESCRIPTION EXTRACTION
# =========================================================

def extract_jd_responsibilities(jd: dict) -> list[str]:

    responsibilities = jd.get("responsibilities", [])

    if isinstance(responsibilities, str):
        responsibilities = split_into_chunks(responsibilities)

    if not isinstance(responsibilities, list):
        return []

    result = []

    for item in responsibilities:

        if isinstance(item, dict):
            item = (
                item.get("description")
                or item.get("responsibility")
                or item.get("text")
                or ""
            )

        item = clean_text(item)

        if item:
            result.append(item)

    return result


# =========================================================
# 5. EXPERIENCE EVIDENCE EXTRACTION
# =========================================================

def extract_experience_text(resume: dict) -> list[dict]:

    evidence = []

    experiences = resume.get("experience", [])

    if not isinstance(experiences, list):
        return evidence

    for experience in experiences:

        if not isinstance(experience, dict):
            continue

        role = clean_text(
            experience.get("role")
            or experience.get("position")
            or experience.get("title")
        )

        company = clean_text(experience.get("company"))

        responsibilities = clean_text_list(
            experience.get("responsibilities")
            or experience.get("description")
            or experience.get("details")
        )

        for responsibility in responsibilities:

            evidence.append({
                "source_type": "experience",
                "role": role,
                "company": company,
                "text": (
                    f"Role: {role}. "
                    f"Company: {company}. "
                    f"Responsibility: {responsibility}"
                ),
                "original_text": responsibility
            })

    return evidence


# =========================================================
# 6. PROJECT EVIDENCE EXTRACTION
# =========================================================

def extract_project_text(resume: dict) -> list[dict]:

    evidence = []

    projects = resume.get("projects", [])

    if not isinstance(projects, list):
        return evidence

    for project in projects:

        if not isinstance(project, dict):
            continue

        project_name = clean_text(project.get("name"))

        description = clean_text(
            project.get("description")
            or project.get("details")
        )

        technologies = clean_text_list(
            project.get("technologies")
            or project.get("skills")
        )

        technology_text = ", ".join(technologies)

        chunks = split_into_chunks(description)

        for chunk in chunks:

            evidence.append({
                "source_type": "project",
                "project_name": project_name,
                "text": (
                    f"Project: {project_name}. "
                    f"Technologies: {technology_text}. "
                    f"Description: {chunk}"
                ),
                "original_text": chunk
            })

    return evidence


# =========================================================
# 7. COLLECT ALL CANDIDATE EVIDENCE
# =========================================================

def extract_candidate_evidence(resume: dict) -> list[dict]:

    return (
        extract_experience_text(resume)
        + extract_project_text(resume)
    )


# =========================================================
# 8. SIMILARITY MATRIX
# =========================================================

def calculate_similarity_matrix(
    responsibilities: list[str],
    evidence: list[dict]
) -> np.ndarray:

    if not responsibilities or not evidence:
        return np.zeros(
            (len(responsibilities), len(evidence)),
            dtype=np.float32
        )

    responsibility_texts = [
        clean_text(item)
        for item in responsibilities
    ]

    evidence_texts = [
        clean_text(item.get("text", ""))
        for item in evidence
    ]

    if not all(responsibility_texts):
        raise ValueError(
            "A JD responsibility contains empty text."
        )

    if not all(evidence_texts):
        raise ValueError(
            "A candidate evidence item contains empty text."
        )

    responsibility_embeddings = generate_embeddings(
        responsibility_texts
    )

    evidence_embeddings = generate_embeddings(
        evidence_texts
    )

    similarity_matrix = np.dot(
        responsibility_embeddings,
        evidence_embeddings.T
    )

    return similarity_matrix


# =========================================================
# 9. FORMAT EVIDENCE MATCH
# =========================================================

def format_evidence_match(
    evidence_item: dict,
    similarity: float
) -> dict:

    return {
        "source_type": evidence_item.get("source_type"),
        "similarity": round(similarity, 4),
        "similarity_score": round(similarity * 100, 2),
        "evidence_strength": classify_similarity(similarity),
        "is_relevant": similarity >= RELEVANCE_THRESHOLD,
        "evidence": (
            evidence_item.get("original_text")
            or evidence_item.get("text")
        ),
        "context": evidence_item
    }


# =========================================================
# 10. RETRIEVE TOP K EVIDENCE
# =========================================================

def get_top_source_matches(
    similarity_row: np.ndarray,
    evidence: list[dict],
    source_type: str,
    top_k: int = TOP_K_EVIDENCE
) -> list[dict]:
    """
    Retrieve the top K matching evidence items
    from experience or projects.
    """

    source_indices = [
        index
        for index, item in enumerate(evidence)
        if item.get("source_type") == source_type
    ]

    if not source_indices:
        return []

    sorted_indices = sorted(
        source_indices,
        key=lambda index: float(similarity_row[index]),
        reverse=True
    )

    top_indices = sorted_indices[:top_k]

    return [
        format_evidence_match(
            evidence[index],
            float(similarity_row[index])
        )
        for index in top_indices
    ]


def get_top_overall_matches(
    similarity_row: np.ndarray,
    evidence: list[dict],
    top_k: int = TOP_K_EVIDENCE
) -> list[dict]:
    """
    Retrieve the top K matches across all evidence sources.
    """

    if not evidence:
        return []

    sorted_indices = sorted(
        range(len(evidence)),
        key=lambda index: float(similarity_row[index]),
        reverse=True
    )

    top_indices = sorted_indices[:top_k]

    return [
        format_evidence_match(
            evidence[index],
            float(similarity_row[index])
        )
        for index in top_indices
    ]


# =========================================================
# 11. FIND BEST SOURCE MATCH
# =========================================================

def get_best_source_match(
    similarity_row: np.ndarray,
    evidence: list[dict],
    source_type: str
) -> dict | None:

    top_matches = get_top_source_matches(
        similarity_row,
        evidence,
        source_type,
        top_k=1
    )

    return top_matches[0] if top_matches else None


# =========================================================
# 12. MATCH JD RESPONSIBILITIES
# =========================================================

def match_responsibilities(
    responsibilities: list[str],
    evidence: list[dict],
    similarity_matrix: np.ndarray
) -> list[dict]:

    matches = []

    for index, responsibility in enumerate(responsibilities):

        similarity_row = similarity_matrix[index]

        experience_top_matches = get_top_source_matches(
            similarity_row,
            evidence,
            "experience"
        )

        project_top_matches = get_top_source_matches(
            similarity_row,
            evidence,
            "project"
        )

        overall_top_matches = get_top_overall_matches(
            similarity_row,
            evidence
        )

        experience_match = (
            experience_top_matches[0]
            if experience_top_matches else None
        )

        project_match = (
            project_top_matches[0]
            if project_top_matches else None
        )

        best_overall = (
            overall_top_matches[0]
            if overall_top_matches else None
        )

        matches.append({

            "responsibility": responsibility,

            "experience_match": experience_match,
            "project_match": project_match,
            "best_overall_match": best_overall,

            "top_experience_matches": experience_top_matches,
            "top_project_matches": project_top_matches,
            "top_overall_matches": overall_top_matches

        })

    return matches


# =========================================================
# 13. CALCULATE SOURCE SCORES
# =========================================================

def calculate_source_scores(matches: list[dict]) -> dict:

    experience_scores = []
    project_scores = []
    overall_scores = []

    experience_assignments = 0
    project_assignments = 0

    experience_strength = {
        "strong": 0,
        "moderate": 0,
        "weak": 0
    }

    project_strength = {
        "strong": 0,
        "moderate": 0,
        "weak": 0
    }

    for item in matches:

        experience_match = item["experience_match"]
        project_match = item["project_match"]
        overall_match = item["best_overall_match"]

        if experience_match is not None:

            experience_scores.append(
                experience_match["similarity"]
            )

            experience_strength[
                experience_match["evidence_strength"]
            ] += 1

        if project_match is not None:

            project_scores.append(
                project_match["similarity"]
            )

            project_strength[
                project_match["evidence_strength"]
            ] += 1

        if overall_match is not None:

            overall_scores.append(
                overall_match["similarity"]
            )

            if overall_match["source_type"] == "experience":
                experience_assignments += 1

            elif overall_match["source_type"] == "project":
                project_assignments += 1

    experience_score = (
        float(np.mean(experience_scores)) * 100
        if experience_scores else 0.0
    )

    project_score = (
        float(np.mean(project_scores)) * 100
        if project_scores else 0.0
    )

    overall_score = (
        float(np.mean(overall_scores)) * 100
        if overall_scores else 0.0
    )

    experience_relevant = (
        experience_strength["strong"]
        + experience_strength["moderate"]
    )

    project_relevant = (
        project_strength["strong"]
        + project_strength["moderate"]
    )

    return {

        "experience_semantic_score": round(
            experience_score, 2
        ),

        "project_semantic_score": round(
            project_score, 2
        ),

        "overall_semantic_score": round(
            overall_score, 2
        ),

        "experience_relevant_matches": experience_relevant,
        "project_relevant_matches": project_relevant,

        "experience_evidence_strength": experience_strength,
        "project_evidence_strength": project_strength,

        "responsibilities_matched_to_experience": (
            experience_assignments
        ),

        "responsibilities_matched_to_projects": (
            project_assignments
        ),

        "relevance_threshold": RELEVANCE_THRESHOLD,
        "strong_similarity_threshold": STRONG_SIMILARITY_LIMIT,
        "top_k_evidence": TOP_K_EVIDENCE
    }


# =========================================================
# 14. MAIN SEMANTIC MATCHING PIPELINE
# =========================================================

def evaluate_semantic_match(
    resume: dict,
    jd: dict
) -> dict:
    """Execute the complete semantic matching pipeline."""

    responsibilities = extract_jd_responsibilities(jd)

    experience_evidence = extract_experience_text(resume)
    project_evidence = extract_project_text(resume)

    all_evidence = (
        experience_evidence + project_evidence
    )

    if not responsibilities:
        raise ValueError(
            "No responsibilities were found in the job description."
        )

    if not all_evidence:
        raise ValueError(
            "No experience or project evidence was found in the resume."
        )

    similarity_matrix = calculate_similarity_matrix(
        responsibilities,
        all_evidence
    )

    matches = match_responsibilities(
        responsibilities,
        all_evidence,
        similarity_matrix
    )

    scores = calculate_source_scores(matches)

    return {

        "status": "success",

        "total_responsibilities": len(responsibilities),

        "total_candidate_evidence": len(all_evidence),

        "total_experience_evidence": len(experience_evidence),

        "total_project_evidence": len(project_evidence),

        **scores,

        "responsibility_matches": matches

    }
