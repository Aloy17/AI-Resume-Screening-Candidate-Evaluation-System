
import re


# ==================================================
# 1. DEGREE LEVELS
# ==================================================

DEGREE_LEVELS = {
    "high_school": 1,
    "diploma": 2,
    "associate": 3,
    "bachelor": 4,
    "master": 5,
    "doctorate": 6,
}

DEGREE_ALIASES = {
    "phd": "doctorate",
    "ph d": "doctorate",
    "doctorate": "doctorate",
    "doctoral": "doctorate",

    "mca": "master",
    "mba": "master",
    "msc": "master",
    "m sc": "master",
    "mtech": "master",
    "m tech": "master",
    "ma": "master",
    "m com": "master",
    "master": "master",
    "masters": "master",

    "bca": "bachelor",
    "bba": "bachelor",
    "bsc": "bachelor",
    "b sc": "bachelor",
    "btech": "bachelor",
    "b tech": "bachelor",
    "ba": "bachelor",
    "b com": "bachelor",
    "bachelor": "bachelor",
    "bachelors": "bachelor",

    "diploma": "diploma",
    "associate": "associate",
    "high school": "high_school",
}


# ==================================================
# 2. FIELD ALIASES
# ==================================================

FIELD_ALIASES = {
    "computer application": "computer science",
    "computer applications": "computer science",
    "computer science": "computer science",
    "information technology": "information technology",
    "data science": "data science",
    "business analytics": "business analytics",
    "business analysis": "business analytics",
    "statistics": "statistics",
    "mathematics": "mathematics",
    "maths": "mathematics",
    "electronics": "electronics",
    "engineering": "engineering",
    "finance": "finance",
    "management": "management",
    "business administration": "business administration",
}


# ==================================================
# 3. TEXT NORMALIZATION
# ==================================================

def normalize_text(text):
    """
    Convert text into lowercase normalized text.
    """

    if not text:
        return ""

    text = str(text).lower()
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ==================================================
# 4. IDENTIFY DEGREE LEVEL
# ==================================================

def identify_degree_level(degree):
    """
    Identify the academic level of a qualification.
    """

    text = normalize_text(degree)

    if not text:
        return None

    aliases = sorted(
        DEGREE_ALIASES.items(),
        key=lambda item: len(item[0]),
        reverse=True
    )

    for alias, level in aliases:

        pattern = r"\b" + re.escape(alias) + r"\b"

        if re.search(pattern, text):
            return level

    return None


# ==================================================
# 5. EXTRACT FIELDS OF STUDY
# ==================================================

def extract_fields_of_study(text):
    """
    Identify academic fields from qualification
    and additional education details.
    """

    normalized = normalize_text(text)

    matched_fields = set()

    aliases = sorted(
        FIELD_ALIASES.items(),
        key=lambda item: len(item[0]),
        reverse=True
    )

    for alias, standard_field in aliases:

        pattern = r"\b" + re.escape(alias) + r"\b"

        if re.search(pattern, normalized):
            matched_fields.add(standard_field)

    return sorted(matched_fields)


# ==================================================
# 6. EXTRACT CANDIDATE EDUCATION
# ==================================================

def extract_candidate_education(resume):
    """
    Extract education information from the output
    of info_extractor.py.

    Supports:
    - qualification
    - degree
    - degree_abbreviation
    - additional_details as a list or string
    """

    education_entries = resume.get("education", [])

    if isinstance(education_entries, dict):
        education_entries = [education_entries]

    candidate_education = []

    for entry in education_entries:

        if not isinstance(entry, dict):
            continue

        # Your parser uses 'qualification'.
        degree = (
            entry.get("qualification")
            or entry.get("degree")
            or ""
        )

        abbreviation = entry.get(
            "degree_abbreviation", ""
        )

        institution = entry.get(
            "institution", ""
        )

        additional_details = entry.get(
            "additional_details", []
        )

        # Handle additional_details as a list or string.
        if isinstance(additional_details, list):
            details_text = " ".join(
                str(item) for item in additional_details
            )

        else:
            details_text = str(additional_details)

        combined_degree = (
            f"{degree} {abbreviation}"
        ).strip()

        combined_text = (
            f"{combined_degree} {details_text}"
        )

        degree_level = identify_degree_level(
            combined_degree
        )

        fields = extract_fields_of_study(
            combined_text
        )

        candidate_education.append({

            "degree": combined_degree,

            "degree_abbreviation": abbreviation,

            "degree_level": degree_level,

            "institution": institution,

            "fields_of_study": fields,

            "additional_details": details_text,

            "duration": entry.get("duration", ""),

        })

    return candidate_education


# ==================================================
# 7. ANALYZE CANDIDATE EDUCATION
# ==================================================

def analyze_candidate_education(resume):

    return extract_candidate_education(resume)


# ==================================================
# 8. ANALYZE JOB DESCRIPTION EDUCATION
# ==================================================

def analyze_jd_education(jd):
    """
    Support both dictionary-based and list-based
    education requirements.

    Your current JD extractor returns a list:

    [
        "Bachelor's degree in Computer Science...",
        "Master's degree in Data Science is preferred."
    ]
    """

    education = jd.get("education_required", [])

    mandatory = []
    preferred = []

    if isinstance(education, str):
        education = [education]

    if isinstance(education, list):

        for requirement in education:

            if not isinstance(requirement, str):
                continue

            normalized = normalize_text(requirement)

            if (
                "preferred" in normalized
                or "desirable" in normalized
                or "optional" in normalized
            ):
                preferred.append(requirement)

            else:
                mandatory.append(requirement)

    elif isinstance(education, dict):

        mandatory = education.get(
            "mandatory",
            education.get("required", [])
        )

        preferred = education.get(
            "preferred", []
        )

        if isinstance(mandatory, str):
            mandatory = [mandatory]

        if isinstance(preferred, str):
            preferred = [preferred]

    return {
        "mandatory_requirements": mandatory,
        "preferred_requirements": preferred,
    }


# ==================================================
# 9. COMPARE DEGREE LEVELS
# ==================================================

def compare_degree_levels(candidate_level, required_level):
    """
    A candidate meets a degree-level requirement
    if their degree is at the required level or higher.
    """

    if not candidate_level or not required_level:
        return False

    candidate_value = DEGREE_LEVELS.get(
        candidate_level
    )

    required_value = DEGREE_LEVELS.get(
        required_level
    )

    if candidate_value is None or required_value is None:
        return False

    return candidate_value >= required_value


# ==================================================
# 10. COMPARE FIELDS
# ==================================================

def compare_fields(candidate_fields, required_fields):
    """
    Compare candidate academic fields with the
    fields mentioned in the JD.
    """

    candidate_fields = set(candidate_fields)
    required_fields = set(required_fields)

    if not required_fields:

        return {
            "matched_fields": [],
            "missing_fields": [],
            "match_percentage": None,
        }

    matched = sorted(
        candidate_fields.intersection(required_fields)
    )

    missing = sorted(
        required_fields.difference(candidate_fields)
    )

    percentage = (
        len(matched) / len(required_fields)
    ) * 100

    return {
        "matched_fields": matched,
        "missing_fields": missing,
        "match_percentage": round(percentage, 2),
    }


# ==================================================
# 11. EVALUATE ONE EDUCATION REQUIREMENT
# ==================================================

def evaluate_single_requirement(
    requirement,
    candidate_education
):
    """
    Compare one JD education requirement against
    all candidate qualifications.

    Select the qualification with the strongest
    combined degree and field match.
    """

    required_level = identify_degree_level(
        requirement
    )

    required_fields = extract_fields_of_study(
        requirement
    )

    if not candidate_education:

        return {
            "requirement": requirement,
            "candidate_degree": None,
            "candidate_institution": None,
            "candidate_degree_level": None,
            "degree_level_match": False,
            "field_match": compare_fields(
                [], required_fields
            ),
            "meets_requirement": False,
        }

    best_match = None
    best_score = -1

    for candidate in candidate_education:

        candidate_level = candidate.get(
            "degree_level"
        )

        # Degree comparison
        if required_level:

            degree_match = compare_degree_levels(
                candidate_level,
                required_level
            )

        else:
            degree_match = None

        # Field comparison
        field_result = compare_fields(
            candidate.get("fields_of_study", []),
            required_fields
        )

        field_percentage = field_result[
            "match_percentage"
        ]

        # Combined selection score
        degree_score = (
            100 if degree_match else 0
        ) if required_level else 0

        field_score = (
            field_percentage
            if field_percentage is not None
            else 0
        )

        if required_level and required_fields:

            combined_score = (
                degree_score * 0.6
                + field_score * 0.4
            )

        elif required_level:

            combined_score = degree_score

        elif required_fields:

            combined_score = field_score

        else:

            combined_score = 0

        # Determine whether this qualification
        # actually satisfies the requirement.
        degree_satisfied = (
            degree_match is not False
        )

        field_satisfied = (
            field_percentage is None
            or field_percentage > 0
        )

        meets_requirement = (
            degree_satisfied and field_satisfied
        )

        result = {

            "requirement": requirement,

            "candidate_degree": candidate.get(
                "degree"
            ),

            "candidate_institution": candidate.get(
                "institution"
            ),

            "candidate_degree_level": candidate_level,

            "degree_level_match": degree_match,

            "field_match": field_result,

            "meets_requirement": meets_requirement,

            "combined_score": round(
                combined_score, 2
            ),

        }

        if combined_score > best_score:

            best_score = combined_score
            best_match = result

    return best_match


# ==================================================
# 12. EVALUATE REQUIREMENT CATEGORY
# ==================================================

def evaluate_requirement_category(
    requirements,
    candidate_education
):
    """
    Evaluate all requirements in one category.
    """

    details = []

    for requirement in requirements:

        result = evaluate_single_requirement(
            requirement,
            candidate_education
        )

        details.append(result)

    total = len(details)

    matched = sum(
        1
        for item in details
        if item["meets_requirement"]
    )

    missing = total - matched

    percentage = (
        (matched / total) * 100
        if total > 0
        else 100.0
    )

    return {
        "total": total,
        "matched": matched,
        "missing": missing,
        "match_percentage": round(
            percentage, 2
        ),
        "details": details,
    }


# ==================================================
# 13. MAIN EDUCATION MATCHING FUNCTION
# ==================================================

def evaluate_education_match(resume, jd):
    """
    Main function for education matching.

    Mandatory requirements: 70%
    Preferred requirements: 30%

    If only one category exists, use its score.
    """

    candidate_education = analyze_candidate_education(
        resume
    )

    jd_education = analyze_jd_education(jd)

    mandatory_requirements = jd_education[
        "mandatory_requirements"
    ]

    preferred_requirements = jd_education[
        "preferred_requirements"
    ]

    mandatory_result = evaluate_requirement_category(
        mandatory_requirements,
        candidate_education
    )

    preferred_result = evaluate_requirement_category(
        preferred_requirements,
        candidate_education
    )

    mandatory_percentage = mandatory_result[
        "match_percentage"
    ]

    preferred_percentage = preferred_result[
        "match_percentage"
    ]

    if mandatory_requirements and preferred_requirements:

        overall_percentage = (
            mandatory_percentage * 0.7
            + preferred_percentage * 0.3
        )

    elif mandatory_requirements:

        overall_percentage = mandatory_percentage

    elif preferred_requirements:

        overall_percentage = preferred_percentage

    else:

        overall_percentage = 100.0

    return {

        "candidate_education": candidate_education,

        "mandatory_requirements": mandatory_result,

        "preferred_requirements": preferred_result,

        "overall_education_match_percentage": round(
            overall_percentage, 2
        ),

    }
