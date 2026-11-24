
import re


# ==========================================================
# 1. SKILL ALIASES
# ==========================================================

SKILL_ALIASES = {
    "js": "javascript",
    "javascript": "javascript",

    "py": "python",

    "powerbi": "power bi",
    "power bi": "power bi",

    "ms excel": "excel",
    "microsoft excel": "excel",

    "postgres": "postgresql",
    "postgre sql": "postgresql",

    "mysql": "mysql",

    "sklearn": "scikit-learn",
    "scikit learn": "scikit-learn",

    "ml": "machine learning",

    "nlp": "natural language processing",

    "aws cloud": "aws",
    "amazon web services": "aws",

    "microsoft azure": "azure",

    "gcp": "google cloud",
    "google cloud platform": "google cloud",

    "rest api": "rest apis",
    "api": "rest apis",

    "git version control": "git",

    "ms sql": "sql server",
    "mssql": "sql server",

    "eda": "exploratory data analysis",
}


# ==========================================================
# 2. NORMALIZE SKILL NAMES
# ==========================================================

def normalize_skill(skill: str) -> str:
    """
    Normalize a skill name for consistent comparison.

    Example:
        JS -> javascript
        PowerBI -> power bi
        NLP -> natural language processing
    """

    if not isinstance(skill, str):
        return ""

    skill = skill.strip().lower()

    skill = re.sub(r"\s+", " ", skill)

    skill = SKILL_ALIASES.get(skill, skill)

    return skill


# ==========================================================
# 3. NORMALIZE SKILL LIST
# ==========================================================

def normalize_skill_list(skills: list) -> list:
    """
    Normalize a list of skills and remove duplicates.
    """

    if not isinstance(skills, (list, tuple, set)):
        raise TypeError("Skills must be provided as a list.")

    normalized_skills = []

    for skill in skills:

        normalized = normalize_skill(skill)

        if normalized and normalized not in normalized_skills:
            normalized_skills.append(normalized)

    return normalized_skills


# ==========================================================
# 4. MATCH TWO SKILL LISTS
# ==========================================================

def compare_skills(candidate_skills: list, job_skills: list) -> dict:
    """
    Compare candidate skills with job requirements.

    Returns:
        matched skills
        missing skills
        match percentage
    """

    candidate_normalized = normalize_skill_list(
        candidate_skills
    )

    job_normalized = normalize_skill_list(
        job_skills
    )

    candidate_set = set(candidate_normalized)

    matched = [
        skill
        for skill in job_normalized
        if skill in candidate_set
    ]

    missing = [
        skill
        for skill in job_normalized
        if skill not in candidate_set
    ]

    total_required = len(job_normalized)

    if total_required == 0:
        match_percentage = 0.0

    else:
        match_percentage = (
            len(matched) / total_required
        ) * 100

    return {
        "matched_skills": matched,
        "missing_skills": missing,
        "total_job_skills": total_required,
        "total_matched": len(matched),
        "match_percentage": round(match_percentage, 2),
    }


# ==========================================================
# 5. EVALUATE REQUIRED AND PREFERRED SKILLS
# ==========================================================

def evaluate_skill_match(
    resume_information: dict,
    jd_information: dict
) -> dict:
    """
    Evaluate a candidate's skills against a job description.

    Required skills and preferred skills are evaluated
    separately.
    """

    if not isinstance(resume_information, dict):
        raise TypeError("Resume information must be a dictionary.")

    if not isinstance(jd_information, dict):
        raise TypeError("JD information must be a dictionary.")

    candidate_skills = resume_information.get(
        "skills", []
    )

    required_skills = jd_information.get(
        "required_skills", []
    )

    preferred_skills = jd_information.get(
        "preferred_skills", []
    )

    required_result = compare_skills(
        candidate_skills,
        required_skills
    )

    preferred_result = compare_skills(
        candidate_skills,
        preferred_skills
    )

    # Required skills receive 70% weight.
    # Preferred skills receive 30% weight.

    if required_result["total_job_skills"] > 0:

        if preferred_result["total_job_skills"] > 0:

            overall_score = (
                required_result["match_percentage"] * 0.70
                +
                preferred_result["match_percentage"] * 0.30
            )

        else:

            overall_score = required_result["match_percentage"]

    elif preferred_result["total_job_skills"] > 0:

        overall_score = preferred_result["match_percentage"]

    else:

        overall_score = 0.0

    return {
        "candidate_skills": normalize_skill_list(
            candidate_skills
        ),

        "required_skill_match": required_result,

        "preferred_skill_match": preferred_result,

        "overall_skill_match_percentage": round(
            overall_score, 2
        ),
    }
