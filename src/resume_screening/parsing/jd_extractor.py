
import re
from pathlib import Path


# ==========================================================
# 1. SKILL DATABASE
# ==========================================================

SKILL_DATABASE = [
    "Natural Language Processing",
    "Exploratory Data Analysis",
    "Data Visualization",
    "Data Warehousing",
    "Hypothesis Testing",
    "Machine Learning",
    "Deep Learning",
    "Generative AI",
    "Critical Thinking",
    "Problem Solving",
    "Project Management",
    "Apache Spark",
    "Scikit-learn",
    "Power BI",
    "Google Cloud",
    "REST APIs",
    "SQL Server",
    "PostgreSQL",
    "TensorFlow",
    "PyTorch",
    "Matplotlib",
    "JavaScript",
    "Node.js",
    "BigQuery",
    "Snowflake",
    "Kubernetes",
    "Communication",
    "Data Analysis",
    "Data Analytics",
    "Data Cleaning",
    "Data Modeling",
    "Statistics",
    "Probability",
    "NumPy",
    "Pandas",
    "Tableau",
    "Seaborn",
    "Excel",
    "Python",
    "Java",
    "React",
    "HTML",
    "CSS",
    "MySQL",
    "MongoDB",
    "Hadoop",
    "AWS",
    "Azure",
    "ETL",
    "GitHub",
    "Git",
    "Docker",
    "Leadership",
    "Teamwork",
    "C++",
    "C",
    "R",
    "SQL",
    "PowerPoint",
]

SKILL_DATABASE = sorted(
    set(SKILL_DATABASE),
    key=len,
    reverse=True
)


# ==========================================================
# 2. SECTION PATTERNS
# ==========================================================

SECTION_PATTERNS = {

    "about_company": [
        r"about\s+(?:the\s+)?company",
        r"company\s+overview",
        r"who\s+we\s+are",
    ],

    "job_overview": [
        r"job\s+overview",
        r"role\s+overview",
        r"position\s+overview",
        r"job\s+summary",
        r"role\s+summary",
        r"about\s+the\s+role",
        r"job\s+description",
    ],

    "responsibilities": [
        r"key\s+responsibilities",
        r"roles\s+and\s+responsibilities",
        r"responsibilities",
        r"what\s+you(?:'ll| will)\s+do",
    ],

    "required_skills": [
        r"required\s+technical\s+skills",
        r"technical\s+skills",
        r"required\s+skills",
        r"mandatory\s+skills",
        r"minimum\s+qualifications",
        r"required\s+qualifications",
    ],

    "preferred_skills": [
        r"preferred\s+skills",
        r"good\s+to\s+have",
        r"preferred\s+qualifications",
        r"desired\s+skills",
        r"additional\s+skills",
    ],

    "education": [
        r"educational\s+qualifications",
        r"education\s+requirements",
        r"education",
        r"academic\s+qualifications",
    ],

    "experience": [
        r"experience\s+requirements",
        r"professional\s+experience",
        r"experience",
    ],

    "soft_skills": [
        r"soft\s+skills",
        r"interpersonal\s+skills",
        r"behavioral\s+skills",
    ],

    "performance_expectations": [
        r"performance\s+expectations",
        r"success\s+criteria",
        r"key\s+performance\s+indicators",
    ],

    "keywords": [
        r"keywords",
        r"job\s+keywords",
    ],
}


# ==========================================================
# 3. TEXT CLEANING
# ==========================================================

def clean_text(text: str) -> str:
    """
    Normalize whitespace and remove unnecessary spaces.
    """

    if not isinstance(text, str):
        raise TypeError("Input must be a string.")

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ==========================================================
# 4. IDENTIFY SECTION HEADINGS
# ==========================================================

def identify_heading(line: str):
    """
    Identify whether a line is a known JD heading.
    """

    heading = line.strip().lower()

    heading = re.sub(r"[:\-]+$", "", heading)
    heading = re.sub(r"\s+", " ", heading)

    for section_name, patterns in SECTION_PATTERNS.items():

        for pattern in patterns:

            if re.fullmatch(pattern, heading):
                return section_name

    return None


# ==========================================================
# 5. IDENTIFY JD SECTIONS
# ==========================================================

def identify_jd_sections(text: str) -> dict:
    """
    Divide the job description into separate sections.
    """

    sections = {}
    current_section = None
    general_lines = []

    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        heading = identify_heading(line)

        if heading:

            current_section = heading

            if heading not in sections:
                sections[heading] = []

            continue

        if current_section:

            sections[current_section].append(line)

        else:

            general_lines.append(line)

    sections["general_information"] = general_lines

    return {
        key: "\n".join(value).strip()
        for key, value in sections.items()
    }


# ==========================================================
# 6. EXTRACT BULLET POINTS
# ==========================================================

def extract_bullet_points(text: str) -> list:
    """
    Extract numbered and bulleted content.
    Joins wrapped lines belonging to the same bullet.
    """

    if not text:
        return []

    items = []

    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        is_bullet = bool(
            re.match(
                r"^(?:[•●▪◦*-]|\d+[.)])\s*",
                line
            )
        )

        if is_bullet:

            line = re.sub(
                r"^(?:[•●▪◦*-]|\d+[.)])\s*",
                "",
                line
            )

            if line:
                items.append(line.strip())

        elif items:

            items[-1] += " " + line

        else:

            items.append(line)

    return [
        re.sub(r"\s+", " ", item).strip()
        for item in items
        if item.strip()
    ]


# ==========================================================
# 7. EXTRACT SKILLS
# ==========================================================

def extract_skills_from_text(text: str) -> list:
    """
    Identify known skills appearing in a text section.

    Checks complete skill names to reduce false matches.
    """

    if not text:
        return []

    found_skills = []
    normalized_text = text.lower()

    for skill in SKILL_DATABASE:

        pattern = (
            r"(?<![a-z0-9+#])"
            + re.escape(skill.lower())
            + r"(?![a-z0-9+#])"
        )

        if re.search(pattern, normalized_text):

            found_skills.append(skill)

    return found_skills


# ==========================================================
# 8. EXTRACT KEYWORDS
# ==========================================================

def extract_keywords(text: str) -> list:
    """
    Split a keyword section into individual keywords.
    """

    if not text:
        return []

    keywords = []

    for item in re.split(r"[,;\n]", text):

        item = item.strip()

        item = re.sub(
            r"^(?:[•●▪◦*-]|\d+[.)])\s*",
            "",
            item
        )

        item = item.strip().rstrip(".")

        if item and item.lower() not in {
            keyword.lower() for keyword in keywords
        }:

            keywords.append(item)

    return keywords


# ==========================================================
# 9. EXTRACT EXPERIENCE REQUIREMENTS
# ==========================================================

def extract_experience_requirement(text: str) -> dict:
    """
    Extract minimum and maximum years of experience.

    Examples:
        2-4 years
        3+ years
        at least 2 years
        minimum 1 year
    """

    result = {
        "minimum": None,
        "maximum": None,
        "unit": "years",
        "raw": None,
    }

    if not text:
        return result

    patterns = [

        r"(\d+(?:\.\d+)?)\s*(?:-|–|—|to)\s*(\d+(?:\.\d+)?)\s*\+?\s*years?",

        r"(\d+(?:\.\d+)?)\s*\+\s*years?",

        r"(?:at\s+least|minimum\s+of|min(?:imum)?)\s+(\d+(?:\.\d+)?)\s+years?",

        r"(\d+(?:\.\d+)?)\s+years?",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if not match:
            continue

        result["raw"] = match.group(0)

        result["minimum"] = float(match.group(1))

        if len(match.groups()) == 2:
            result["maximum"] = float(match.group(2))

        break

    for key in ["minimum", "maximum"]:

        value = result[key]

        if value is not None and value.is_integer():
            result[key] = int(value)

    return result


# ==========================================================
# 10. EXTRACT HEADER INFORMATION
# ==========================================================

def extract_header_information(lines: list) -> dict:
    """
    Extract basic job information from the JD header.
    """

    result = {
        "job_title": None,
        "company": None,
        "department": None,
        "job_type": None,
        "location": None,
        "work_mode": None,
    }

    patterns = {

        "company":
            r"^(?:company|organization)\s*:\s*(.+)$",

        "department":
            r"^department\s*:\s*(.+)$",

        "job_type":
            r"^(?:employment\s+type|job\s+type)\s*:\s*(.+)$",

        "location":
            r"^location\s*:\s*(.+)$",

        "work_mode":
            r"^(?:work\s+mode|work\s+arrangement)\s*:\s*(.+)$",
    }

    for line in lines:

        for field, pattern in patterns.items():

            match = re.match(
                pattern,
                line,
                re.IGNORECASE
            )

            if match:
                result[field] = match.group(1).strip()

        title_match = re.match(
            r"^(?:job\s+title|position|role)\s*:\s*(.+)$",
            line,
            re.IGNORECASE
        )

        if title_match:
            result["job_title"] = title_match.group(1).strip()

    # If no explicit title label exists,
    # use the first line as the job title.

    if not result["job_title"] and lines:

        first_line = lines[0]

        if not re.match(
            r"^(company|organization|department|location|employment type|job type)\s*:",
            first_line,
            re.IGNORECASE
        ):

            result["job_title"] = first_line

    return result


# ==========================================================
# 11. EXTRACT EDUCATION
# ==========================================================

def extract_education(section_text: str) -> list:
    """
    Extract educational qualifications.
    """

    return extract_bullet_points(section_text)


# ==========================================================
# 12. MAIN JD EXTRACTION FUNCTION
# ==========================================================

def extract_job_description_information(text: str) -> dict:
    """
    Main function.

    Accepts raw job description text and returns
    structured job description information.
    """

    text = clean_text(text)

    if not text:

        raise ValueError(
            "Job description is empty. "
            "Please provide actual JD text."
        )

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    # Identify sections.

    sections = identify_jd_sections(text)

    # Extract header.

    header = extract_header_information(lines)

    # Extract experience.

    experience_text = " ".join([

        sections.get("experience", ""),

        sections.get("required_skills", ""),

        sections.get("job_overview", ""),

    ])

    experience = extract_experience_requirement(
        experience_text
    )

    # Extract required skills.

    required_skills = extract_skills_from_text(
        sections.get("required_skills", "")
    )

    # Extract preferred skills.

    preferred_skills = extract_skills_from_text(
        sections.get("preferred_skills", "")
    )

    # Extract responsibilities.

    responsibilities = extract_bullet_points(
        sections.get("responsibilities", "")
    )

    # Extract soft skills.

    soft_skills = extract_bullet_points(
        sections.get("soft_skills", "")
    )

    # Extract education.

    education = extract_education(
        sections.get("education", "")
    )

    # Extract performance expectations.

    performance_expectations = extract_bullet_points(
        sections.get("performance_expectations", "")
    )

    # Extract individual keywords.

    keywords = extract_keywords(
        sections.get("keywords", "")
    )

    # Fallback if no keyword section exists.

    if not keywords:

        keywords = list(dict.fromkeys(
            required_skills + preferred_skills
        ))

    # Build final structured output.

    result = {

        **header,

        "experience_required": experience,

        "required_skills": required_skills,

        "preferred_skills": preferred_skills,

        "education_required": education,

        "responsibilities": responsibilities,

        "soft_skills": soft_skills,

        "about_company": sections.get(
            "about_company", ""
        ),

        "job_overview": sections.get(
            "job_overview", ""
        ),

        "performance_expectations": performance_expectations,

        "keywords": keywords,

        "sections": sections,
    }

    return result


# ==========================================================
# 13. EXTRACT JD FROM TEXT FILE
# ==========================================================

def extract_jd_from_file(file_path: str) -> dict:
    """
    Read a .txt job description and extract its information.
    """

    path = Path(file_path)

    if not path.exists():

        raise FileNotFoundError(
            f"Job description file not found: {path}"
        )

    if path.suffix.lower() != ".txt":

        raise ValueError(
            "Currently, only .txt JD files are supported."
        )

    text = path.read_text(encoding="utf-8")

    if not text.strip():

        raise ValueError(
            f"The job description file is empty: {path}"
        )

    return extract_job_description_information(text)
