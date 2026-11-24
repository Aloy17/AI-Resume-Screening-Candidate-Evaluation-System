"""Transparent five-category weighted candidate scoring."""
from __future__ import annotations

CATEGORIES = ("skills", "experience", "education", "projects", "certifications")
WEIGHT_PROFILES = {
    "software_development": {"skills": .25, "experience": .15, "education": .20, "projects": .30, "certifications": .10},
    "cloud_devops": {"skills": .20, "experience": .30, "education": .10, "projects": .10, "certifications": .30},
    "cybersecurity": {"skills": .20, "experience": .30, "education": .10, "projects": .10, "certifications": .30},
    "default": {"skills": .30, "experience": .25, "education": .15, "projects": .20, "certifications": .10},
}

def determine_weights(jd: dict) -> dict[str, float]:
    """Select a documented profile from the role; no generative/opaque weighting."""
    title = str(jd.get("job_title") or jd.get("title") or "").lower()
    responsibilities = jd.get("responsibilities") or []
    if isinstance(responsibilities, str):
        responsibilities = [responsibilities]
    text = " ".join([title, str(jd.get("job_overview") or ""), *map(str, responsibilities)]).lower()
    if any(k in text for k in ("devops", "cloud engineer", "site reliability", "platform engineer")):
        profile = "cloud_devops"
    elif any(k in text for k in ("cybersecurity", "security analyst", "penetration tester", "information security")):
        profile = "cybersecurity"
    elif any(k in text for k in ("developer", "software engineer", "mobile", "application engineer", "python")):
        profile = "software_development"
    else:
        profile = "default"
    return dict(WEIGHT_PROFILES[profile])

def calculate_final_score(category_scores: dict, weights: dict | None = None) -> dict:
    """Reweight only across categories that can actually be evaluated."""
    configured = dict(weights or WEIGHT_PROFILES["default"])
    if set(configured) != set(CATEGORIES):
        raise ValueError(f"Weights must define exactly: {', '.join(CATEGORIES)}")
    if any(not isinstance(v, (int, float)) or v < 0 for v in configured.values()) or sum(configured.values()) <= 0:
        raise ValueError("Weights must be non-negative numbers with a positive total.")
    total = sum(configured.values())
    configured = {k: v / total for k, v in configured.items()}
    available = {k: max(0.0, min(100.0, float(category_scores[k])))
                 for k in CATEGORIES if category_scores.get(k) is not None and configured[k] > 0}
    if not available:
        return {"final_score": 0.0, "category_scores": category_scores,
                "weights_configured": configured, "weights_applied": {},
                "excluded_categories": list(CATEGORIES)}
    denominator = sum(configured[k] for k in available)
    applied = {k: configured[k] / denominator for k in available}
    score = sum(available[k] * applied[k] for k in available)
    return {"final_score": round(score, 2), "category_scores": category_scores,
            "weights_configured": configured, "weights_applied": applied,
            "excluded_categories": [k for k in CATEGORIES if k not in available]}
