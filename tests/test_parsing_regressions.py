from resume_screening.parsing.info_extractor import (
    _extract_education, _extract_experience, _extract_projects,
)

CANDIDATE_9_EDUCATION = """Master of Computer Applications (MCA) – Cybersecurity | ITM Skills University | 2026–2028
Bachelor of Computer Applications (BCA) | Bharati Vidyapeeth (Deemed to be University), Department of
Management Studies | 2024–2026
INTEREST
Cybersecurity and Ethical Hacking
Network Security
"""

CANDIDATE_17_EXPERIENCE = """Hari Om Thalassic Pvt. Ltd.









Full-Stack Developer Intern
Developed scalable web applications using the MERN stack and Django. May 2025 – August 2025
Built a maritime training portal to streamline training management processes.
Built dynamic and responsive user interfaces to enhance the overall user experience.
"""

CANDIDATE_9_PROJECTS = """WebShield – Website Security Checker
Worked on a project to check website-related security information and help identify potential security concerns.
Technologies: Python, Supabase, Web Security.
The Cyber Minds – Cybersecurity Awareness Initiative
Created cybersecurity awareness content covering topics such as data protection, cyber laws and online safety.
Focus: Cybersecurity Awareness, Digital Safety, Content Research.
Password Strength Analyzer – Practice Project
A proposed beginner project to assess password strength using length, character variety and common-pattern checks.
Suggested technologies: Python, Regular Expressions.
Status: Suggested project; include as completed only after implementation.
"""


def test_education_parses_degree_first_pipe_separated_records():
    entries = _extract_education(CANDIDATE_9_EDUCATION)
    assert len(entries) == 2
    assert entries[0].degree.startswith("Master of Computer Applications")
    assert entries[0].institution == "ITM Skills University"
    assert entries[0].year == 2028
    assert entries[1].degree.startswith("Bachelor of Computer Applications")
    assert "Bharati Vidyapeeth" in entries[1].institution
    assert "Management Studies" in entries[1].institution
    assert entries[1].year == 2026


def test_experience_parses_company_title_and_inline_date():
    entries = _extract_experience(CANDIDATE_17_EXPERIENCE)
    assert len(entries) == 1
    assert entries[0].company == "Hari Om Thalassic Pvt. Ltd."
    assert entries[0].title == "Full-Stack Developer Intern"
    assert entries[0].duration_months == 4
    assert len(entries[0].responsibilities) == 3
    assert "MERN stack and Django" in entries[0].responsibilities[0]


def test_experience_section_absence_produces_no_entries():
    assert _extract_experience("") == []


def test_projects_split_consecutive_headings_and_skip_proposed_work():
    entries = _extract_projects(CANDIDATE_9_PROJECTS)
    assert len(entries) == 2
    assert entries[0].name == "WebShield – Website Security Checker"
    assert entries[1].name == "The Cyber Minds – Cybersecurity Awareness Initiative"
    assert all("Password Strength Analyzer" not in item.name for item in entries)
