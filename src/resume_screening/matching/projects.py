"""Project-specific semantic matching, reusing the shared evidence matcher."""
from src.resume_screening.matching.semantic import (
    extract_project_text, extract_jd_responsibilities,
    calculate_similarity_matrix, get_top_source_matches,
)
import numpy as np

def evaluate_project_match(resume: dict, jd: dict) -> dict:
    projects = extract_project_text(resume)
    responsibilities = extract_jd_responsibilities(jd)
    if not projects or not responsibilities:
        return {"score": None, "evidence": [], "status": "not_evaluable"}
    matrix = calculate_similarity_matrix(responsibilities, projects)
    best_by_requirement = matrix.max(axis=1)
    evidence = []
    for index, requirement in enumerate(responsibilities):
        matches = get_top_source_matches(matrix[index], projects, "project", top_k=1)
        evidence.append({"jd_responsibility": requirement, "best_project_match": matches[0] if matches else None})
    score = float(np.mean(best_by_requirement)) * 100
    return {"score": round(max(0.0, min(100.0, score)), 2), "evidence": evidence, "status": "scored"}
