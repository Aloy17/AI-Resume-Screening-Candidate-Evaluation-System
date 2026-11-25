
from __future__ import annotations

import re
from datetime import date

from ..models import (
    EducationEntry,
    ExperienceEntry,
    ExtractionStatus,
    JobDescription,
    ProjectEntry,
    ResumeData,
)


# --------------------------------------------------
# 1. Section headings and skill dictionary
# --------------------------------------------------

SECTION_HEADINGS = {
    "skills": {
        "skills",
        "technical skills",
        "technical proficiencies",
        "technical proficiency",
        "technical expertise",
        "core competencies",
        "core skills",
        "technical competencies",
        "technologies",
        "tools and technologies",
        "technology stack",
        "proficiencies",
    },
    "experience": {
        "experience",
        "work experience",
        "professional experience",
        "career experience",
        "career history",
        "employment history",
        "employment",
        "professional history",
        "work history",
        "internship experience",
        "internships",
        "internship / work experience",
    },
    "education": {
        "education",
        "academic background",
        "academic history",
        "academic qualifications",
        "educational qualifications",
        "qualifications",
        "training",
    },
    "projects": {
        "projects",
        "key projects",
        "selected projects",
        "notable projects",
        "technical projects",
        "project highlights",
        "academic projects",
        "personal projects",
        "project experience",
    },
    "responsibilities": {
        "responsibilities",
        "key responsibilities",
        "job responsibilities",
        "roles and responsibilities",
    },
    "requirements": {
        "requirements",
        "qualifications required",
        "required qualifications",
        "job requirements",
    },
}


SKILL_KEYWORDS = {
    # Programming languages
    "python": ["python"],
    "java": ["java"],
    "c": ["c programming", "c language"],
    "c++": ["c++"],
    "c#": ["c#"],
    "javascript": [
        "javascript",
        "java script",
        "javascript es6",
        "javascript (es6",
    ],
    "typescript": ["typescript", "type script"],
    "kotlin": ["kotlin"],
    "dart": ["dart"],
    "bash": ["bash"],
    "shell scripting": ["shell scripting", "shell script"],

    # Web development
    "html": ["html", "html5", "semantic html", "semantic html5"],
    "css": ["css", "css3", "modern css", "modern css3"],
    "react": ["react", "react.js", "reactjs"],
    "vue": ["vue", "vue.js"],
    "react native": ["react native"],
    "next.js": ["next.js", "nextjs"],
    "angular": ["angular"],
    "tailwind css": ["tailwind css", "tailwind"],
    "vite": ["vite"],
    "webpack": ["webpack"],
    "node.js": ["node.js", "nodejs"],
    "express.js": ["express.js"],
    "django": ["django"],
    "flask": ["flask"],
    "fastapi": ["fastapi"],
    "flutter": ["flutter"],

    # Databases and APIs
    "sql": ["sql"],
    "mysql": ["mysql"],
    "postgresql": ["postgresql", "postgres"],
    "mongodb": ["mongodb"],
    "redis": ["redis"],
    "sqlite": ["sqlite"],
    "room": ["android room", "room database"],
    "firebase": ["firebase"],
    "supabase": ["supabase"],
    "rest apis": ["rest api", "rest apis"],

    # Version control and development tools
    "git": ["git"],
    "github": ["github"],
    "github actions": ["github actions"],
    "gitlab ci": ["gitlab ci", "gitlab ci/cd"],
    "jenkins": ["jenkins"],
    "pytest": ["pytest"],
    "unittest": ["unittest"],

    # DevOps and cloud
    "docker": ["docker"],
    "kubernetes": ["kubernetes"],
    "terraform": ["terraform"],
    "ansible": ["ansible"],
    "aws": ["aws", "amazon web services"],
    "azure": ["azure", "microsoft azure"],
    "gcp": ["gcp", "google cloud platform"],
    "linux": ["linux"],
    "windows": ["windows"],
    "ci/cd": ["ci/cd", "continuous integration", "continuous deployment"],
    "infrastructure as code": ["infrastructure as code", "iac"],
    "cloud computing": ["cloud computing"],
    "cloud security": ["cloud security"],
    "prometheus": ["prometheus"],
    "grafana": ["grafana"],
    "elk stack": ["elk stack", "elasticsearch logstash kibana"],
    "http": ["http", "https"],
    "tcp/ip": ["tcp/ip", "tcp ip"],
    "dns": ["dns", "domain name system"],
    "networking": ["networking", "network fundamentals"],

    # Cybersecurity
    "cybersecurity": ["cybersecurity", "cyber security"],
    "network security": ["network security"],
    "vulnerability assessment": [
        "vulnerability assessment",
        "vulnerability assessments",
    ],
    "penetration testing": ["penetration testing", "penetration test"],
    "security testing": ["security testing"],
    "security monitoring": ["security monitoring"],
    "threat detection": ["threat detection"],
    "siem": ["siem"],
    "splunk": ["splunk"],
    "ibm qradar": ["ibm qradar", "qradar"],
    "microsoft sentinel": ["microsoft sentinel", "sentinel"],
    "firewalls": ["firewall", "firewalls"],
    "ids": [
        "ids",
        "intrusion detection system",
        "intrusion detection systems",
    ],
    "ips": [
        "ips",
        "intrusion prevention system",
        "intrusion prevention systems",
    ],
    "encryption": ["encryption"],
    "authentication": ["authentication"],
    "access control": ["access control"],
    "owasp top 10": ["owasp top 10"],
    "incident response": ["incident response"],
    "security audits": ["security audit", "security audits"],
    "mitre att&ck": ["mitre att&ck", "mitre attack"],
    "nist cybersecurity framework": ["nist cybersecurity framework"],
    "identity management": ["identity management"],
    "digital forensics": ["digital forensics"],
    "malware analysis": ["malware analysis"],
    "iso 27001": ["iso 27001"],

    # Mobile development
    "android development": [
        "android development",
        "android applications",
    ],
    "mobile application development": [
        "mobile application development",
        "mobile app development",
    ],
    "mobile ui/ux": ["mobile ui/ux", "mobile ui", "mobile ux"],
    "android jetpack": ["android jetpack", "jetpack components"],
    "state management": ["state management"],
    "google play store": ["google play store", "play store publishing"],
    "mobile application security": [
        "mobile application security",
        "mobile app security",
    ],
    "local storage": ["local storage"],

    # Machine learning and data science
    "machine learning": ["machine learning"],
    "deep learning": ["deep learning"],
    "natural language processing": [
        "natural language processing",
        "nlp",
    ],
    "tensorflow": ["tensorflow"],
    "pytorch": ["pytorch"],
    "scikit-learn": ["scikit-learn", "sklearn"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "power bi": ["power bi"],
    "tableau": ["tableau"],
    "excel": ["excel", "microsoft excel"],

    # AI tools and frameworks
    "gemini": ["gemini", "google gemini"],
    "genkit": ["genkit"],
    "rag": ["rag", "rag pipelines"],
    "recharts": ["recharts"],
    "claude": ["claude", "anthropic claude"],
    "prompt engineering": ["prompt engineering"],
}


# --------------------------------------------------
# 2. General helper functions
# --------------------------------------------------

def _clean_invisible_characters(text: str) -> str:
    """Remove formatting characters that PDF text commonly adds by mistake."""

    return re.sub(r"[\u200b\u2060\ufeff]", "", text)


def _normalize_heading(line: str) -> str:
    """Normalize a possible resume section heading."""

    line = _clean_invisible_characters(line)
    line = line.strip().lower()
    line = re.sub(r"^\s*(?:\d+\s*[.)]|[•●▪◦*])\s*", "", line)
    line = re.sub(r"[:\-–—]+$", "", line)
    line = re.sub(r"[^a-z0-9 &/]+", "", line)

    return re.sub(r"\s+", " ", line).strip()


def _extract_sections(text: str) -> dict[str, str]:
    """Divide resume text into recognized sections."""

    heading_lookup = {}

    for section, headings in SECTION_HEADINGS.items():
        for heading in headings:
            heading_lookup[heading] = section

    sections = {"other": []}
    current_section = "other"

    for line in text.splitlines():
        normalized = _normalize_heading(line)

        if normalized in heading_lookup:
            current_section = heading_lookup[normalized]
            sections.setdefault(current_section, [])
        else:
            sections[current_section].append(line)

    return {
        name: "\n".join(lines).strip()
        for name, lines in sections.items()
    }


def _extract_skills(text: str) -> list[str]:
    """Identify known skills using keyword matching."""

    found = set()
    normalized_text = _clean_invisible_characters(text).lower()

    for skill, aliases in SKILL_KEYWORDS.items():
        for alias in aliases:
            pattern = (
                r"(?<!\w)"
                + re.escape(alias)
                + r"(?!\w)"
            )

            if re.search(pattern, normalized_text):
                # Avoid classifying React Native as React.
                if skill == "react" and re.search(
                    r"\breact\s+native\b",
                    normalized_text,
                ):
                    continue

                found.add(skill)
                break

    return sorted(found)


def _clean_bullet(line: str) -> str:
    """Remove common bullet characters and invisible characters."""

    line = _clean_invisible_characters(line)

    return re.sub(
        r"^\s*[•●▪◦*+\-]\s*",
        "",
        line,
    ).strip()


def _split_blocks(text: str) -> list[str]:
    """Split text into non-empty paragraphs."""

    return [
        block.strip()
        for block in re.split(r"\n\s*\n", text)
        if block.strip()
    ]


def _split_experience_blocks(text: str) -> list[str]:
    """Split compact experience text at consecutive pipe-separated role lines."""

    blocks = []
    role_markers = (
        "intern", "engineer", "developer", "manager",
        "analyst", "consultant", "specialist", "coordinator",
        "lead", "associate", "director", "executive",
    )

    for block in _split_blocks(text):
        lines = [
            line.strip()
            for line in block.splitlines()
            if line.strip()
        ]
        role_indexes = [
            index for index, line in enumerate(lines)
            if "|" in line
            and any(marker in line.lower() for marker in role_markers)
        ]

        if len(role_indexes) < 2:
            blocks.append(block)
            continue

        starts = role_indexes
        for position, start in enumerate(starts):
            end = starts[position + 1] if position + 1 < len(starts) else len(lines)
            segment = "\n".join(lines[start:end]).strip()
            if segment:
                blocks.append(segment)

    return blocks


def _section_status(
    sections: dict[str, str],
    section_name: str,
    extracted_count: int,
) -> ExtractionStatus:
    """Describe extraction state without turning it into a downstream score."""

    if section_name not in sections:
        return ExtractionStatus.MISSING

    raw_section = sections.get(section_name, "").strip()
    if not raw_section:
        return ExtractionStatus.EMPTY

    if extracted_count > 0:
        return ExtractionStatus.EXTRACTED

    return ExtractionStatus.AMBIGUOUS


# --------------------------------------------------
# 3. Date extraction
# --------------------------------------------------

MONTH_PATTERN = (
    r"Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|"
    r"May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|"
    r"Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?"
)

DATE_PATTERN = re.compile(
    rf"(?P<start_month>{MONTH_PATTERN})?"
    rf"\s*(?P<start_year>19\d{{2}}|20\d{{2}})"
    rf"\s*(?:-|–|—|to)\s*"
    rf"(?:(?P<end_month>{MONTH_PATTERN})?"
    rf"\s*(?P<end_year>19\d{{2}}|20\d{{2}}|present|current))",
    re.IGNORECASE,
)

NUMERIC_DATE_RANGE_PATTERN = re.compile(
    r"(?P<start>"
    r"(?:19\d{2}|20\d{2})(?:[-/](?:0?[1-9]|1[0-2]))?"
    r"|(?:0?[1-9]|1[0-2])[-/](?:19\d{2}|20\d{2})"
    r")"
    r"\s*(?:-|–|—|to)\s*"
    r"(?P<end>"
    r"(?:19\d{2}|20\d{2})(?:[-/](?:0?[1-9]|1[0-2]))?"
    r"|(?:0?[1-9]|1[0-2])[-/](?:19\d{2}|20\d{2})"
    r"|present|current"
    r")",
    re.IGNORECASE,
)


MONTHS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}


def _month_index(
    month: str | None,
    year: str,
    is_end: bool,
) -> int:
    """Convert a date into a month index."""

    year_number = (
        date.today().year
        if year.lower() in {"present", "current"}
        else int(year)
    )

    if month:
        month_number = MONTHS[month[:3].lower()]
    else:
        month_number = 12 if is_end else 1

    return year_number * 12 + month_number


def _get_date_range_months(
    text: str,
) -> tuple[int, int] | None:
    """Return the inclusive start and end month indices."""

    match = DATE_PATTERN.search(text)
    if match:
        start = _month_index(
            match.group("start_month"),
            match.group("start_year"),
            False,
        )

        end = _month_index(
            match.group("end_month"),
            match.group("end_year"),
            True,
        )
    else:
        numeric_match = NUMERIC_DATE_RANGE_PATTERN.search(text)
        if not numeric_match:
            return None

        def parse_numeric(value: str, is_end: bool) -> int:
            value = value.strip().lower()
            if value in {"present", "current"}:
                year_number = date.today().year
                month_number = 12 if is_end else 1
                return year_number * 12 + month_number

            if "-" in value:
                left, right = value.split("-", 1)
                if left.isdigit() and len(left) == 4:
                    return int(left) * 12 + (int(right) if right.isdigit() else (12 if is_end else 1))
                return int(right) * 12 + int(left)

            if "/" in value:
                left, right = value.split("/", 1)
                if left.isdigit() and len(left) == 4:
                    return int(left) * 12 + (int(right) if right.isdigit() else (12 if is_end else 1))
                return int(right) * 12 + int(left)

            year_number = int(value)
            return year_number * 12 + (12 if is_end else 1)

        start = parse_numeric(numeric_match.group("start"), False)
        end = parse_numeric(numeric_match.group("end"), True)

    if end < start:
        return None

    return start, end


def _get_duration_months(text: str) -> float | None:
    """Calculate the duration of one experience entry."""

    date_range = _get_date_range_months(text)

    if date_range is None:
        return None

    start, end = date_range

    return float(end - start + 1)


def _get_total_experience_months(text: str) -> int:
    """Calculate total experience without double-counting overlaps."""

    intervals = []

    for block in _split_experience_blocks(text):
        date_range = _get_date_range_months(block)

        if date_range:
            intervals.append(date_range)

    if not intervals:
        return 0

    intervals.sort()

    total_months = 0
    current_start, current_end = intervals[0]

    for start, end in intervals[1:]:
        if start <= current_end + 1:
            current_end = max(current_end, end)
        else:
            total_months += current_end - current_start + 1
            current_start, current_end = start, end

    total_months += current_end - current_start + 1

    return total_months


# --------------------------------------------------
# 4. Experience extraction
# --------------------------------------------------

def _extract_experience(text: str) -> list[ExperienceEntry]:
    """Extract experience entries from compact and whitespace-heavy layouts."""

    # PDF extraction can leave zero-width characters on otherwise blank lines.
    # Remove them before splitting blocks so a company name remains the
    # immediately preceding block of its role instead of being separated
    # by invisible-only blocks.
    text = _clean_invisible_characters(text)

    entries = []
    blocks = _split_experience_blocks(text)

    for block_index, block in enumerate(blocks):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        date_location = None
        for line_index, line in enumerate(lines):
            match = DATE_PATTERN.search(line)
            if match:
                date_location = (line_index, match)
                break
        if date_location is None:
            numeric_match = NUMERIC_DATE_RANGE_PATTERN.search(block)
            if numeric_match:
                for line_index, line in enumerate(lines):
                    if NUMERIC_DATE_RANGE_PATTERN.search(line):
                        date_location = (line_index, numeric_match)
                        break
        if date_location is None:
            if not lines:
                continue

            first_line = _clean_bullet(lines[0])
            role_markers = (
                "intern", "engineer", "developer", "manager",
                "analyst", "consultant", "specialist", "coordinator",
                "lead", "associate", "director", "executive",
            )

            if "|" in first_line:
                title, company = [
                    part.strip()
                    for part in first_line.split("|", 1)
                ]
            elif any(marker in first_line.lower() for marker in role_markers):
                title, company = first_line, ""
            else:
                continue

            responsibilities = [
                _clean_bullet(line)
                for line in lines[1:]
                if _clean_bullet(line)
            ]

            entries.append(
                ExperienceEntry(
                    title=title,
                    company=company,
                    duration_months=None,
                    responsibilities=list(dict.fromkeys(responsibilities)),
                )
            )
            continue

        date_index, date_match = date_location
        before_date = lines[:date_index]
        after_date = lines[date_index + 1:]
        inline_prefix = lines[date_index][:date_match.start()].strip()
        inline_suffix = lines[date_index][date_match.end():].strip()

        company = ""
        title = ""
        responsibilities = []

        if len(before_date) >= 2:
            company = _clean_bullet(before_date[0])
            title = _clean_bullet(before_date[1])
            responsibilities.extend(_clean_bullet(line) for line in before_date[2:])
        elif len(before_date) == 1:
            title = _clean_bullet(before_date[0])
            if block_index > 0:
                previous_lines = [
                    line.strip()
                    for line in blocks[block_index - 1].splitlines()
                    if line.strip()
                ]
                if len(previous_lines) == 1:
                    company = _clean_bullet(previous_lines[0])

        if inline_prefix and inline_prefix != title:
            responsibilities.append(_clean_bullet(inline_prefix))
        if inline_suffix:
            responsibilities.append(_clean_bullet(inline_suffix))
        responsibilities.extend(
            _clean_bullet(line) for line in after_date if _clean_bullet(line)
        )
        responsibilities = list(dict.fromkeys(
            item for item in responsibilities if item
        ))

        entries.append(
            ExperienceEntry(
                title=title,
                company=company,
                duration_months=_get_duration_months(lines[date_index]),
                responsibilities=responsibilities,
            )
        )

    return entries



# --------------------------------------------------
# 5. Education extraction
# --------------------------------------------------

DEGREE_KEYWORDS = [
    "bachelor",
    "master",
    "b.tech",
    "m.tech",
    "bca",
    "mca",
    "b.sc",
    "m.sc",
    "b.com",
    "m.com",
    "mba",
    "phd",
    "diploma",
    "b.e.",
    "m.e.",
    "bba",
    "hsc",
    "ssc",
    "higher secondary",
    "secondary school",
    "ba",
    "ma",
]


DEGREE_PATTERN = re.compile(
    r"\b(master|bachelor|b\.?sc|m\.?sc|b\.?ca|m\.?ca|"
    r"b\.?com|m\.?com|b\.?tech|m\.?tech|mba|phd|"
    r"diploma|hsc|ssc|bba|b\.?e|m\.?e)\b",
    re.IGNORECASE,
)


INSTITUTION_PATTERN = re.compile(
    r"\b(university|college|school|institute|institution)\b|\[.+\]",
    re.IGNORECASE,
)


YEAR_PATTERN = re.compile(r"(?:19|20)\d{2}")


def _get_field_of_study(degree: str) -> str:
    """Infer a field of study from the degree name."""

    normalized = degree.lower()

    if (
        "computer applications" in normalized
        or re.search(r"\bmca\b|\bbca\b", normalized)
    ):
        return "Computer Applications"

    if "computer science" in normalized:
        return "Computer Science"

    if "information technology" in normalized:
        return "Information Technology"

    if "business administration" in normalized or re.search(
        r"\bmba\b|\bbba\b",
        normalized,
    ):
        return "Business Administration"

    if "data science" in normalized:
        return "Data Science"

    return ""


def _extract_education(text: str) -> list[EducationEntry]:
    """Extract education records from degree-first and institution-first layouts."""

    # Normalize invisible PDF formatting characters before parsing degree
    # names and institution text.
    text = _clean_invisible_characters(text)

    entries = []
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    stop_headings = {
        "interest", "interests", "language", "languages",
        "skills", "projects", "certifications", "achievements",
    }

    for index, line in enumerate(lines):
        if not DEGREE_PATTERN.search(line):
            continue

        parts = [part.strip(" []") for part in re.split(r"\s*\|\s*", line)]
        if len(parts) == 1:
            parts = [
                part.strip()
                for part in re.split(r"\s+[–—-]\s+", line)
            ]

        # Match degree names only at the beginning of a segment.
        # Searching anywhere would misread ordinary words such as "be"
        # in "Deemed to be University" as the abbreviation "B.E.".
        degree_part = next(
            (part for part in parts if DEGREE_PATTERN.match(part)),
            None,
        )
        if degree_part is None:
            degree_part = line

        degree = YEAR_PATTERN.sub("", degree_part).strip(" |,–—-")
        institution_parts = [
            part for part in parts
            if part != degree_part
            and not YEAR_PATTERN.search(part)
            and not re.fullmatch(r"(?i)pursuing|present|current", part.strip())
            and not DEGREE_PATTERN.match(part)
        ]
        institution = " ".join(
            part.strip(" ,") for part in institution_parts
        ).strip()

        years = YEAR_PATTERN.findall(line)
        year = int(years[-1]) if years else None

        if institution and re.search(r"\b(of|at|in|the)$", institution, re.IGNORECASE):
            for following in lines[index + 1:]:
                normalized = _normalize_heading(following)
                if normalized in stop_headings or DEGREE_PATTERN.search(following):
                    break
                following_years = YEAR_PATTERN.findall(following)
                continuation = YEAR_PATTERN.sub("", following).strip(" |,–—-")
                if continuation and not re.fullmatch(
                    r"(?i)pursuing|present|current", continuation
                ):
                    institution = f"{institution} {continuation}".strip()
                if following_years:
                    year = int(following_years[-1])
                    break

        identity = (degree.lower(), institution.lower(), year)
        if any(
            (item.degree.lower(), item.institution.lower(), item.year) == identity
            for item in entries
        ):
            continue

        entries.append(
            EducationEntry(
                degree=degree,
                field_of_study=_get_field_of_study(degree),
                institution=institution,
                year=year,
            )
        )

    return entries



# --------------------------------------------------
# 6. Project extraction
# --------------------------------------------------

def _extract_projects(text: str) -> list[ProjectEntry]:
    """Extract projects even when PDF text has no blank lines between them."""

    entries = []
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    heading_pattern = re.compile(r"^.{2,90}\s+[–—]\s+.{2,90}$")
    pipe_heading_pattern = re.compile(r"^.{2,90}\s*\|\s*.{2,90}$")
    labeled_heading_pattern = re.compile(
        r"^.{2,60}\s*:\s*.{2,90}$",
        re.IGNORECASE,
    )
    heading_indexes = [
        index for index, line in enumerate(lines)
        if (
            heading_pattern.match(line)
            or pipe_heading_pattern.match(line)
            or (
                re.match(r"(?i)^project\s+\d*\s*[:\-]", line)
                is not None
            )
            or (
                index + 1 < len(lines)
                and re.match(r"^\s*[•●▪◦*+\-]\s*", lines[index + 1])
                and not re.match(
                    r"(?i)^(technologies|technology|tech stack|tools|focus|status)\s*:",
                    line,
                )
                and "|" not in line
                and ":" not in line
                and "," not in line
                and "." not in line
            )
            or (
                labeled_heading_pattern.match(line)
                and not re.match(
                    r"(?i)^(technologies|technology|tech stack|tools|focus|status)\s*:",
                    line,
                )
            )
        )
    ]

    if heading_indexes:
        segments = []
        for position, start in enumerate(heading_indexes):
            end = heading_indexes[position + 1] if position + 1 < len(heading_indexes) else len(lines)
            segments.append(lines[start:end])
    else:
        segments = [
            [line.strip() for line in block.splitlines() if line.strip()]
            for block in _split_blocks(text)
        ]

    excluded_status = re.compile(
        r"\b(proposed|suggested project|practice project|not yet implemented|"
        r"include as completed only after implementation)\b",
        re.IGNORECASE,
    )

    for segment in segments:
        if not segment:
            continue
        name = _clean_bullet(segment[0])
        remaining = segment[1:]
        if excluded_status.search(" ".join(remaining)) or excluded_status.search(name):
            continue

        description_lines = []
        metadata_lines = []
        for line in remaining:
            if DATE_PATTERN.search(line):
                continue
            if re.match(r"(?i)^(technologies|technology|tech stack|tools|focus|status)\s*:", line):
                metadata_lines.append(line)
                continue
            if "|" in line or re.search(
                r"\bhttps?://|\b[\w-]+\.vercel\.app\b", line
            ):
                metadata_lines.append(line)
                continue
            description_lines.append(_clean_bullet(line))

        description = " ".join(description_lines)
        technology_text = " ".join(metadata_lines + description_lines)
        entries.append(
            ProjectEntry(
                name=name,
                description=description,
                technologies=_extract_skills(technology_text),
            )
        )

    return entries



# --------------------------------------------------
# 7. Resume parsing
# --------------------------------------------------

def parse_resume(
    clean_text: str,
    candidate_id: str,
    source_file: str = "",
) -> ResumeData:
    """Convert cleaned resume text into structured ResumeData."""

    if not isinstance(clean_text, str):
        raise TypeError("Resume text must be a string.")

    if not clean_text.strip():
        raise ValueError("Resume text cannot be empty.")

    if not candidate_id:
        raise ValueError("Candidate ID cannot be empty.")

    sections = _extract_sections(clean_text)

    skills = _extract_skills(
        sections.get("skills", "")
    )

    experience = _extract_experience(
        sections.get("experience", "")
    )

    education = _extract_education(
        sections.get("education", "")
    )

    projects = _extract_projects(
        sections.get("projects", "")
    )

    total_months = _get_total_experience_months(
        sections.get("experience", "")
    )

    extraction_status = {
        "skills": _section_status(sections, "skills", len(skills)),
        "experience": _section_status(
            sections,
            "experience",
            len(experience),
        ),
        "education": _section_status(
            sections,
            "education",
            len(education),
        ),
        "projects": _section_status(
            sections,
            "projects",
            len(projects),
        ),
    }

    return ResumeData(
        candidate_id=candidate_id,
        source_file=source_file,
        skills=skills,
        experience=experience,
        education=education,
        projects=projects,
        total_experience_years=round(total_months / 12, 2),
        extraction_status=extraction_status,
    )


# --------------------------------------------------
# 8. Job description parsing
# --------------------------------------------------

JD_SECTION_HEADINGS = {
    "job_details": {
        "job details",
    },
    "role_summary": {
        "role summary",
        "job summary",
        "about the role",
    },
    "skills": {
        "required technical skills",
        "technical skills",
        "required skills",
        "required qualifications",
        "minimum qualifications",
        "mandatory skills",
        "must have",
        "core qualifications",
        "skills",
    },
    "experience": {
        "required experience",
        "minimum experience",
        "experience requirements",
        "experience qualification",
        "professional experience",
        "experience required",
        "experience",
    },
    "education": {
        "education requirements",
        "educational requirements",
        "education",
    },
    "certifications": {
        "required certifications",
        "certifications",
        "professional certifications",
    },
    "responsibilities": {
        "key responsibilities",
        "responsibilities",
        "roles and responsibilities",
        "job responsibilities",
        "key duties",
        "duties",
        "what youll do",
        "what you will do",
    },
    "projects": {
        "relevant project experience",
        "project requirements",
        "project deliverables",
        "project experience",
        "key projects",
        "projects",
    },
    "preferred": {
        "preferred qualifications",
        "preferred skills",
        "desirable qualifications",
    },
    "evaluation": {
        "evaluation emphasis",
        "evaluation criteria",
        "selection criteria",
    },
}


def _normalize_jd_heading(line: str) -> str:
    """Normalize numbered job description headings."""

    line = _clean_invisible_characters(line)
    line = line.strip().lower()

    line = re.sub(r"^\s*\d+\s*[.)]\s*", "", line)
    line = re.sub(r"[:\-–—]+$", "", line)
    line = re.sub(r"[^a-z0-9 &/]+", "", line)

    return re.sub(r"\s+", " ", line).strip()


def _extract_jd_sections(text: str) -> dict[str, str]:
    """Extract numbered JD sections."""

    heading_lookup = {
        heading: section
        for section, headings in JD_SECTION_HEADINGS.items()
        for heading in headings
    }

    sections = {}
    current_section = "other"

    for line in text.splitlines():
        normalized = _normalize_jd_heading(line)

        if normalized in heading_lookup:
            current_section = heading_lookup[normalized]
            sections.setdefault(current_section, [])
        else:
            sections.setdefault(current_section, []).append(line)

    return {
        section: "\n".join(lines).strip()
        for section, lines in sections.items()
    }



def _extract_jd_bullets(text: str) -> list[str]:
    """Extract numbered or bulleted items and join wrapped lines."""

    items = []

    for line in text.splitlines():
        line = _clean_invisible_characters(line).strip()

        if not line:
            continue

        # Remove page footers, including those appended to bullet text.
        line = re.sub(
            r"\s*[—–-]\s*.*?\bJob Description\s+Page\s+\d+\s+of\s+\d+.*$",
            "",
            line,
            flags=re.IGNORECASE,
        ).strip()

        if not line:
            continue

        match = re.match(
            r"^(?:\d+\s*[.)]\s*|[•●▪◦*+\-]\s*)(.+)$",
            line,
        )

        if match:
            items.append(match.group(1).strip())
        elif items:
            items[-1] += " " + line

    return [
        item.strip()
        for item in items
        if item.strip()
    ]



def _extract_required_preferred_skills(
    skills_text: str,
    preferred_text: str,
) -> tuple[list[str], list[str]]:
    """Separate explicitly preferred skills from required skills."""

    preferred_markers = (
        "preferred",
        "desirable",
        "optional",
        "nice to have",
        "good to have",
        "would be an advantage",
    )

    required = set()
    preferred = set()

    for bullet in _extract_jd_bullets(skills_text):
        detected = set(_extract_skills(bullet))

        if any(
            marker in bullet.lower()
            for marker in preferred_markers
        ):
            preferred.update(detected)
        else:
            required.update(detected)

    preferred.update(
        _extract_skills(preferred_text)
    )

    return sorted(required), sorted(preferred)


def _extract_experience_range(
    text: str,
) -> tuple[float, float | None]:
    """Extract the minimum and maximum experience requirements."""

    match = re.search(
        r"(\d+(?:\.\d+)?)\s*(?:-|–|—|to)\s*"
        r"(\d+(?:\.\d+)?)\s*\+?\s*years?",
        text,
        re.IGNORECASE,
    )

    if match:
        return (
            float(match.group(1)),
            float(match.group(2)),
        )

    match = re.search(
        r"(\d+(?:\.\d+)?)\s*\+?\s*years?",
        text,
        re.IGNORECASE,
    )

    if match:
        return float(match.group(1)), None

    return 0.0, None


def _extract_jd_education(text: str) -> str:
    """Extract the degree requirement from education text."""

    degree_patterns = [
        (r"\bbachelor(?:'|’)?s?\b", "BACHELOR"),
        (r"\bmaster(?:'|’)?s?\b", "MASTER"),
        (r"\bb\.?\s*tech\b", "B.TECH"),
        (r"\bm\.?\s*tech\b", "M.TECH"),
        (r"\bmca\b", "MCA"),
        (r"\bbca\b", "BCA"),
        (r"\bm\.?\s*sc\b", "M.SC"),
        (r"\bb\.?\s*sc\b", "B.SC"),
        (r"\bmba\b", "MBA"),
        (r"\bph\.?d\b", "PHD"),
        (r"\bdiploma\b", "DIPLOMA"),
    ]

    for pattern, degree in degree_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return degree

    return ""


def _extract_certifications(text: str) -> list[str]:
    """Extract known professional certifications."""

    certification_aliases = {
        "CompTIA Security+": [
            "CompTIA Security+",
            "Security Plus",
        ],
        "Certified Ethical Hacker (CEH)": [
            "Certified Ethical Hacker",
            "CEH",
        ],
        "Certified Information Systems Security Professional (CISSP)": [
            "Certified Information Systems Security Professional",
            "CISSP",
        ],
        "Certified Information Security Manager (CISM)": [
            "Certified Information Security Manager",
            "CISM",
        ],
        "GIAC Security Essentials (GSEC)": [
            "GIAC Security Essentials",
            "GSEC",
        ],
        "CompTIA CySA+": [
            "CompTIA CySA+",
            "CySA+",
        ],
        "AWS Certified Solutions Architect – Associate": [
            "AWS Certified Solutions Architect",
        ],
        "AWS Certified DevOps Engineer – Professional": [
            "AWS Certified DevOps Engineer",
        ],
        "Microsoft Certified: Azure Administrator Associate": [
            "Microsoft Certified: Azure Administrator Associate",
        ],
        "Microsoft Certified: DevOps Engineer Expert": [
            "Microsoft Certified: DevOps Engineer Expert",
        ],
        "Certified Kubernetes Administrator (CKA)": [
            "Certified Kubernetes Administrator",
            "CKA",
        ],
        "HashiCorp Certified: Terraform Associate": [
            "HashiCorp Certified: Terraform Associate",
            "Terraform Associate",
        ],
    }

    found = []

    normalized_text = _clean_invisible_characters(text).lower()

    for certification, aliases in certification_aliases.items():
        for alias in aliases:
            if re.search(
                re.escape(alias.lower()),
                normalized_text,
            ):
                found.append(certification)
                break

    return sorted(set(found))


def _split_required_preferred(
    text: str,
) -> tuple[str, str]:
    """Separate Required and Preferred subsections."""

    match = re.search(
        r"\bPreferred\s*:\s*",
        text,
        re.IGNORECASE,
    )

    if not match:
        return text, ""

    required_text = text[:match.start()]
    preferred_text = text[match.end():]

    return required_text, preferred_text


def parse_job_description(text: str) -> JobDescription:
    """Convert cleaned JD text into structured JobDescription data."""

    if not isinstance(text, str):
        raise TypeError("Job description must be a string.")

    if not text.strip():
        raise ValueError("Job description cannot be empty.")

    text = _clean_invisible_characters(text)

    sections = _extract_jd_sections(text)

    # --------------------------------------------------
    # Job title
    # --------------------------------------------------

    title = ""

    job_details = sections.get("job_details", "")

    title_match = re.search(
        r"Job Title\s*:\s*(.+)",
        job_details,
        re.IGNORECASE,
    )

    if title_match:
        title = title_match.group(1).strip()

    if not title:
        first_line = next(
            (line.strip() for line in text.splitlines() if line.strip()),
            "",
        )

        title = re.sub(
            r"^JOB DESCRIPTION\s*\d*\s*:\s*",
            "",
            first_line,
            flags=re.IGNORECASE,
        )

    title = _clean_invisible_characters(title).strip()

    # --------------------------------------------------
    # Experience
    # --------------------------------------------------

    experience_text = (
        job_details
        + "\n"
        + sections.get("experience", "")
    )

    min_experience, max_experience = (
        _extract_experience_range(experience_text)
    )

    # --------------------------------------------------
    # Skills
    # --------------------------------------------------

    preferred_text = sections.get("preferred", "")

    required_skills, preferred_skills = (
        _extract_required_preferred_skills(
            sections.get("skills", ""),
            preferred_text,
        )
    )

    # --------------------------------------------------
    # Education
    # --------------------------------------------------

    education_text = sections.get("education", "")

    required_education_text, preferred_education_text = (
        _split_required_preferred(education_text)
    )

    required_education = _extract_jd_education(
        required_education_text
    )

    preferred_education = _extract_jd_education(
        preferred_education_text
    )

    # --------------------------------------------------
    # Responsibilities and projects
    # --------------------------------------------------

    responsibilities = _extract_jd_bullets(
        sections.get("responsibilities", "")
    )

    project_requirements = _extract_jd_bullets(
        sections.get("projects", "")
    )

    # --------------------------------------------------
    # Certifications
    # --------------------------------------------------

    certification_text = sections.get("certifications", "")

    if re.search(
        r"preferred\s+professional\s+certifications",
        certification_text,
        re.IGNORECASE,
    ):
        required_certifications = []
        preferred_certifications = _extract_certifications(
            certification_text
        )
    else:
        required_certifications = _extract_certifications(
            certification_text
        )

        preferred_certifications = _extract_certifications(
            preferred_text
        )

    preferred_certifications = sorted(
        set(preferred_certifications)
    )

    # --------------------------------------------------
    # Evaluation emphasis
    # --------------------------------------------------

    evaluation_emphasis = _extract_jd_bullets(
        sections.get("evaluation", "")
    )

    experience_status = ExtractionStatus.MISSING
    if sections.get("experience", "").strip() or job_details.strip():
        experience_status = (
            ExtractionStatus.EXTRACTED
            if min_experience or max_experience is not None
            else ExtractionStatus.AMBIGUOUS
        )

    extraction_status = {
        "title": (
            ExtractionStatus.EXTRACTED
            if title
            else ExtractionStatus.AMBIGUOUS
        ),
        "required_skills": _section_status(
            sections,
            "skills",
            len(required_skills),
        ),
        "preferred_skills": _section_status(
            sections,
            "preferred",
            len(preferred_skills),
        ),
        "experience": experience_status,
        "education": _section_status(
            sections,
            "education",
            1 if required_education or preferred_education else 0,
        ),
        "responsibilities": _section_status(
            sections,
            "responsibilities",
            len(responsibilities),
        ),
        "projects": _section_status(
            sections,
            "projects",
            len(project_requirements),
        ),
        "certifications": _section_status(
            sections,
            "certifications",
            len(required_certifications) + len(preferred_certifications),
        ),
    }

    # --------------------------------------------------
    # Final structured result
    # --------------------------------------------------

    return JobDescription(
        title=title,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        min_experience_years=min_experience,
        max_experience_years=max_experience,
        required_education=required_education,
        preferred_education=preferred_education,
        responsibilities=responsibilities,
        project_requirements=project_requirements,
        required_certifications=required_certifications,
        preferred_certifications=preferred_certifications,
        evaluation_emphasis=evaluation_emphasis,
        raw_text=text,
        extraction_status=extraction_status,
    )
