
import re
from difflib import SequenceMatcher


# =========================================================
# 1. SKILL DATABASE
# =========================================================

SKILL_DATABASE = [
    "Python", "Java", "JavaScript", "SQL",
    "HTML", "CSS", "React", "PHP",
    "Bootstrap", "Tailwind CSS",
    "Natural Language Processing", "BERT",
    "Power BI", "Tableau", "Excel",
    "Data Analysis", "Data Analytics",
    "Data Visualization", "Data Cleaning",
    "Exploratory Data Analysis", "Data Modeling",
    "Statistics", "DSA", "Git", "GitHub",
    "MySQL", "OpenAI API", "Generative AI",
    "TF-IDF", "Project Management",
    "Graphic Design", "Communication",
    "Leadership", "Teamwork"
]

SKILL_ALIASES = {
    "nlp": "Natural Language Processing",
    "eda": "Exploratory Data Analysis"
}


# =========================================================
# 2. SECTION HEADINGS
# =========================================================

SECTION_HEADINGS = {
    "education": [
        "education",
        "academic background",
        "academics"
    ],

    "experience": [
        "experience",
        "work experience",
        "professional experience",
        "internship experience"
    ],

    "projects": [
        "projects",
        "academic projects",
        "personal projects"
    ],

    "extracurricular": [
        "extracurricular",
        "extracurricular activities",
        "activities"
    ],

    "skills_awards": [
        "skills awards",
        "technical skills",
        "skills",
        "technical skills awards"
    ]
}


def normalize_heading(text):
    """Normalize a heading for comparison."""

    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    return re.sub(r"\s+", " ", text).strip()


def match_section_heading(line):
    """Identify resume section headings."""

    normalized = normalize_heading(line)

    for section, aliases in SECTION_HEADINGS.items():

        for alias in aliases:
            alias = normalize_heading(alias)

            if normalized == alias:
                return section

            similarity = SequenceMatcher(
                None,
                normalized,
                alias
            ).ratio()

            if similarity >= 0.88:
                return section

    return None


# =========================================================
# 3. IDENTIFY RESUME SECTIONS
# =========================================================

def identify_sections(text):
    """Separate resume text into individual sections."""

    sections = {
        "education": "",
        "experience": "",
        "projects": "",
        "extracurricular": "",
        "skills_awards": ""
    }

    current_section = None
    general_lines = []

    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        detected_section = match_section_heading(line)

        if detected_section:
            current_section = detected_section
            continue

        if current_section:
            sections[current_section] += line + "\n"

        else:
            general_lines.append(line)

    sections["general"] = "\n".join(general_lines)

    return {
        key: value.strip()
        for key, value in sections.items()
    }


# =========================================================
# 4. CONTACT INFORMATION EXTRACTION
# =========================================================

def extract_contact_information(text):
    """Extract name, email, phone, LinkedIn and portfolio."""

    email_match = re.search(
        r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}",
        text
    )

    phone_match = re.search(
        r"(?:\+?\d[\d\s().-]{8,}\d)",
        text
    )

    linkedin_match = re.search(
        r"(?:linkedin\s*[:\-]?\s*)"
        r"(https?://[^\s]+|www\.[^\s]+)",
        text,
        re.IGNORECASE
    )

    portfolio_match = re.search(
        r"(?:portfolio|website|personal website)"
        r"\s*[:\-]?\s*(https?://[^\s]+|www\.[^\s]+)",
        text,
        re.IGNORECASE
    )

    if linkedin_match:
        linkedin_url = linkedin_match.group(1).rstrip(".,;)")

    else:
        urls = re.findall(r"https?://[^\s]+", text)

        linkedin_url = next(
            (
                url.rstrip(".,;)")
                for url in urls
                if "linkedin.com" in url.lower()
            ),
            None
        )

    if portfolio_match:
        portfolio_url = portfolio_match.group(1).rstrip(".,;)")

    else:
        urls = re.findall(r"https?://[^\s]+", text)

        portfolio_url = next(
            (
                url.rstrip(".,;)")
                for url in urls
                if "linkedin.com" not in url.lower()
            ),
            None
        )

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    name = None

    for line in lines[:5]:

        if (
            not re.search(r"@", line)
            and not re.search(r"\d", line)
            and len(line.split()) <= 5
            and len(line) <= 60
        ):
            name = line
            break

    return {
        "name": name,
        "email": email_match.group(0) if email_match else None,
        "phone": phone_match.group(0).strip() if phone_match else None,
        "linkedin": linkedin_url,
        "portfolio": portfolio_url
    }


# =========================================================
# 5. SKILLS EXTRACTION
# =========================================================

def extract_skills(text):
    """Extract skills and normalize common aliases."""

    found_skills = []
    normalized_text = text.lower()

    for skill in SKILL_DATABASE:

        pattern = (
            r"(?<!\w)"
            + re.escape(skill.lower())
            + r"(?!\w)"
        )

        if re.search(pattern, normalized_text):

            canonical_skill = SKILL_ALIASES.get(
                skill.lower(),
                skill
            )

            if canonical_skill not in found_skills:
                found_skills.append(canonical_skill)

    for alias, canonical in SKILL_ALIASES.items():

        pattern = (
            r"(?<!\w)"
            + re.escape(alias)
            + r"(?!\w)"
        )

        if re.search(pattern, normalized_text):

            if canonical not in found_skills:
                found_skills.append(canonical)

    return found_skills


# =========================================================
# 6. GENERAL TEXT HELPERS
# =========================================================

def clean_line(line):
    """Remove bullet markers and unnecessary whitespace."""

    line = line.strip()

    line = re.sub(
        r"^[•●▪◦■◆\-*]+\s*",
        "",
        line
    )

    return line.strip()


def is_date(line):
    """Identify common date formats."""

    patterns = [
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",

        r"\b\d{4}\s*[-–]\s*\d{4}\b",

        r"\b\d{4}\s*[-–]\s*(?:present|current)\b",

        r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)"
        r"[a-z]*\s+\d{4}\b",

        r"\b\d{4}\b"
    ]

    return any(
        re.search(pattern, line, re.IGNORECASE)
        for pattern in patterns
    )


def is_bullet(line):
    """Check whether a line begins with a bullet."""

    return bool(
        re.match(
            r"^[•●▪◦■◆\-*]\s*",
            line.strip()
        )
    )


# =========================================================
# 7. RESPONSIBILITIES EXTRACTION
# =========================================================

def extract_bullet_points(text):
    """Extract bullets and join wrapped continuation lines."""

    responsibilities = []
    current_bullet = None

    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        if is_bullet(line):

            if current_bullet:
                responsibilities.append(current_bullet)

            current_bullet = clean_line(line)

        elif current_bullet:

            if is_date(line):
                responsibilities.append(current_bullet)
                current_bullet = None

            else:
                current_bullet += " " + line

    if current_bullet:
        responsibilities.append(current_bullet)

    return responsibilities


# =========================================================
# 8. EDUCATION EXTRACTION
# =========================================================

def extract_education(text):
    """
    Extract individual education records.

    Each record contains:
    institution, qualification, duration and additional_details.
    """

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    def is_qualification(line):

        lower = line.lower().strip()

        # Minor and major subjects are additional details,
        # not separate qualifications.
        if lower.startswith(("minor in", "major in")):
            return False

        degree_patterns = [
            r"\bmasters?\b",
            r"\bbachelors?\b",
            r"\bb\.?tech\b",
            r"\bm\.?tech\b",
            r"\bbca\b",
            r"\bmca\b",
            r"\bb\.?sc\b",
            r"\bm\.?sc\b",
            r"\bb\.?com\b",
            r"\bm\.?com\b",
            r"\bbba\b",
            r"\bmba\b",
            r"\bdiploma\b",
            r"\bph\.?d\b",
            r"\bdegree\b"
        ]

        return any(
            re.search(pattern, lower)
            for pattern in degree_patterns
        )

    def is_institution(line):

        lower = line.lower()

        return any(
            word in lower
            for word in [
                "university",
                "college",
                "institute",
                "school"
            ]
        )

    education_records = []

    pending_institution = None
    pending_location = None
    current_record = None

    for line in lines:

        # Identify a new institution.
        if is_institution(line):

            if current_record:
                education_records.append(current_record)
                current_record = None

            pending_institution = line
            pending_location = None

            continue

        # Identify a degree or qualification.
        if is_qualification(line):

            current_record = {
                "institution": pending_institution,
                "qualification": line,
                "duration": None,
                "additional_details": []
            }

            if pending_location:

                current_record["additional_details"].append(
                    pending_location
                )

            pending_institution = None
            pending_location = None

            continue

        # Collect information belonging to the current record.
        if current_record:

            if (
                is_date(line)
                and current_record["duration"] is None
            ):

                current_record["duration"] = line

            else:

                current_record["additional_details"].append(line)

        # Collect institution location before qualification.
        elif pending_institution:

            if pending_location is None:
                pending_location = line

    if current_record:
        education_records.append(current_record)

    return education_records


# =========================================================
# 9. EXPERIENCE EXTRACTION
# =========================================================

def extract_experience(text):
    """
    Extract work experience into separate records.

    Each record contains:
    company, role, duration, location and responsibilities.
    """

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    records = []
    current_record = None

    role_keywords = [
        "intern",
        "developer",
        "engineer",
        "analyst",
        "manager",
        "designer",
        "consultant",
        "assistant",
        "associate",
        "executive",
        "specialist",
        "administrator"
    ]

    def save_current_record():

        if current_record:
            records.append(current_record.copy())

    for line in lines:

        lower_line = line.lower()

        is_role = any(
            keyword in lower_line
            for keyword in role_keywords
        )

        is_company = (
            any(
                term in lower_line
                for term in [
                    "pvt.",
                    "private limited",
                    "solutions",
                    "technologies",
                    "technology",
                    "ltd",
                    "limited",
                    "corporation",
                    "company"
                ]
            )
            and not is_role
            and not is_date(line)
        )

        if is_company:

            save_current_record()

            current_record = {
                "company": line,
                "role": None,
                "duration": None,
                "location": None,
                "responsibilities": []
            }

        elif current_record:

            if (
                is_role
                and current_record["role"] is None
            ):

                current_record["role"] = line

            elif (
                is_date(line)
                and current_record["duration"] is None
            ):

                current_record["duration"] = line

            elif is_bullet(line):

                current_record["responsibilities"].append(
                    clean_line(line)
                )

            elif (
                not current_record["location"]
                and any(
                    word in lower_line
                    for word in [
                        "mumbai",
                        "hybrid",
                        "onsite",
                        "remote"
                    ]
                )
            ):

                current_record["location"] = line

            elif current_record["responsibilities"]:

                current_record["responsibilities"][-1] += (
                    " " + line
                )

            elif not current_record["role"]:

                current_record["role"] = line

            else:

                current_record["responsibilities"].append(line)

    save_current_record()

    return records


# =========================================================
# 10. PROJECT EXTRACTION
# =========================================================

def extract_projects(text):
    """
    Extract projects as separate records.

    Each record contains:
    name, description and technologies.
    """

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    projects = []
    current_project = None

    ignored_lines = [
        "project link",
        "relevant to internship experience"
    ]

    technology_prefixes = [
        "technologies used:",
        "technology used:",
        "tech stack:",
        "tools used:"
    ]

    def save_current_project():

        if current_project:
            projects.append(current_project.copy())

    def clean_technologies(technology_text):

        return [
            item.strip().rstrip(".,;:")
            for item in re.split(r"[,|]", technology_text)
            if item.strip().rstrip(".,;:")
        ]

    for line in lines:

        content = clean_line(line)
        lower_line = content.lower()

        if any(
            lower_line.startswith(item)
            for item in ignored_lines
        ):
            continue

        # Identify technology labels.
        technology_prefix = next(
            (
                prefix
                for prefix in technology_prefixes
                if lower_line.startswith(prefix)
            ),
            None
        )

        if technology_prefix and current_project:

            technology_text = content[
                len(technology_prefix):
            ]

            current_project["technologies"] = (
                clean_technologies(technology_text)
            )

            continue

        # Identify possible project titles.
        is_possible_title = (
            not is_bullet(line)
            and len(content) <= 90
            and not is_date(content)
            and not content.endswith((".", ",", ";"))
            and not re.search(
                r"^(the website|this project|built using|"
                r"the system|and |for |from |with )",
                lower_line
            )
        )

        if is_possible_title:

            if current_project is None:

                current_project = {
                    "name": content,
                    "description": [],
                    "technologies": []
                }

                continue

            if current_project["description"]:

                save_current_project()

                current_project = {
                    "name": content,
                    "description": [],
                    "technologies": []
                }

                continue

        if current_project and content:

            current_project["description"].append(content)

    save_current_project()

    # Join descriptions and identify explicitly mentioned skills.
    for project in projects:

        description = " ".join(
            project["description"]
        ).strip()

        project["description"] = description

        for skill in SKILL_DATABASE:

            pattern = (
                r"(?<!\w)"
                + re.escape(skill)
                + r"(?!\w)"
            )

            if re.search(
                pattern,
                description,
                re.IGNORECASE
            ):

                if skill not in project["technologies"]:
                    project["technologies"].append(skill)

        # Normalize technology aliases.
        for alias, canonical in SKILL_ALIASES.items():

            if re.search(
                r"(?<!\w)" + re.escape(alias) + r"(?!\w)",
                description,
                re.IGNORECASE
            ):

                if canonical not in project["technologies"]:
                    project["technologies"].append(canonical)

    return projects


# =========================================================
# 11. ACHIEVEMENTS EXTRACTION
# =========================================================

def extract_achievements(text):
    """Extract achievement-related statements."""

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    achievements = []

    for index, line in enumerate(lines):

        lower_line = line.lower()

        if any(
            keyword in lower_line
            for keyword in [
                "award",
                "achievement",
                "recipient",
                "honour",
                "honor",
                "scholarship"
            ]
        ):

            achievement = line

            if index + 1 < len(lines):

                next_line = lines[index + 1]

                if (
                    next_line[0].islower()
                    or next_line.lower().startswith("semester")
                ):

                    achievement += " " + next_line

            achievements.append(achievement)

    return achievements


# =========================================================
# 12. MAIN RESUME INFORMATION EXTRACTION
# =========================================================

def extract_resume_information(text):
    """
    Extract structured information from cleaned resume text.

    Returns:
        contact_information
        skills
        education
        experience
        responsibilities
        projects
        extracurricular_activities
        achievements
    """

    if not isinstance(text, str):
        raise TypeError("Resume text must be a string.")

    if not text.strip():
        raise ValueError("Resume text is empty.")

    # Separate resume sections.
    sections = identify_sections(text)

    # Extract contact information.
    contact_information = extract_contact_information(
        sections["general"] + "\n" + text
    )

    # Extract skills.
    skills = extract_skills(
        sections["skills_awards"] + "\n" + text
    )

    # Extract education records.
    education = extract_education(
        sections["education"]
    )

    # Extract experience records.
    experience = extract_experience(
        sections["experience"]
    )

    # Collect responsibilities from all experiences.
    responsibilities = []

    for record in experience:

        responsibilities.extend(
            record["responsibilities"]
        )

    # Extract projects.
    projects = extract_projects(
        sections["projects"]
    )

    # Preserve extracurricular text.
    extracurricular = sections["extracurricular"]

    # Extract achievements.
    achievements = extract_achievements(
        sections["skills_awards"]
    )

    return {
        "contact_information": contact_information,
        "skills": skills,
        "education": education,
        "experience": experience,
        "responsibilities": responsibilities,
        "projects": projects,
        "extracurricular_activities": extracurricular,
        "achievements": achievements
    }
