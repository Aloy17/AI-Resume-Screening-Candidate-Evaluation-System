from pathlib import Path

from resume_screening.extraction import extract_text
from resume_screening.parsing.cleaner import clean_text
from resume_screening.parsing.info_extractor import (
    _extract_education,
    _extract_experience,
    _extract_projects,
    _extract_sections,
    _extract_jd_sections,
    parse_job_description,
    parse_resume,
)
from resume_screening.models import ExtractionStatus, JobDescription, ResumeData

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


CANDIDATE_17_EDUCATION = """ITM Skills University - MCA\u200b
\u200b
\u200b
\u200b
\u200b
\u200b
Pursuing
Bachelor of Computer Science 2026
INTERESTS
Full-Stack Web Development
"""


def test_experience_ignores_invisible_only_lines_between_company_and_role():
    text = CANDIDATE_17_EXPERIENCE.replace(
        "Hari Om Thalassic Pvt. Ltd.\\n",
        "Hari Om Thalassic Pvt. Ltd.\\n" + "\\u200b\\n" * 7,
    )
    entries = _extract_experience(text)
    assert len(entries) == 1
    assert entries[0].company == "Hari Om Thalassic Pvt. Ltd."
    assert entries[0].title == "Full-Stack Developer Intern"


def test_education_parses_institution_first_mca_and_degree_without_institution():
    entries = _extract_education(CANDIDATE_17_EDUCATION)
    assert len(entries) == 2
    assert entries[0].degree == "MCA"
    assert entries[0].institution == "ITM Skills University"
    assert entries[0].year is None
    assert entries[1].degree == "Bachelor of Computer Science"
    assert entries[1].institution == ""
    assert entries[1].year == 2026


def test_explicit_alternate_resume_headings_are_recognized():
    text = """Technical Proficiencies
Python, React
Career History
Software Engineer | Example Corp
Academic Background
Bachelor of Computer Science
Key Projects
Dashboard — Analytics portal
"""
    sections = _extract_sections(text)
    assert "python" in sections["skills"].lower()
    assert "software engineer" in sections["experience"].lower()
    assert "bachelor" in sections["education"].lower()
    assert "dashboard" in sections["projects"].lower()


def test_experience_parses_month_year_and_numeric_ranges():
    month_text = """Senior Developer | Example Corp
Built internal APIs. Jan 2022 – Mar 2024
"""
    numeric_text = """Platform Engineer | Example Ltd
Managed deployments. 01/2023 - 06/2024
"""
    month_entries = _extract_experience(month_text)
    numeric_entries = _extract_experience(numeric_text)
    assert len(month_entries) == 1
    assert month_entries[0].duration_months == 27
    assert len(numeric_entries) == 1
    assert numeric_entries[0].duration_months == 18


def test_experience_parses_undated_role_entries_and_preserves_responsibilities():
    text = """Associate Product Manager and Product Management Intern | BharatNXT
Built a responsive invoice landing page.
Collaborated with engineering and design teams.

Technology and Transformation Intern | Deloitte India
Contributed to technology transformation workflows.
"""
    entries = _extract_experience(text)
    assert len(entries) == 2
    assert entries[0].title.startswith("Associate Product Manager")
    assert entries[0].company == "BharatNXT"
    assert entries[0].duration_months is None
    assert len(entries[0].responsibilities) == 2
    assert entries[1].company == "Deloitte India"


def test_project_layout_supports_pipe_and_labeled_headings():
    pipe_text = """Analytics Dashboard | React and Firebase
Built a real-time operations dashboard.
Technologies: React, Firebase
"""
    labeled_text = """Project: Mobile Inventory App
Built a mobile inventory workflow.
Tech Stack: React Native, Firebase
"""
    pipe_entries = _extract_projects(pipe_text)
    labeled_entries = _extract_projects(labeled_text)
    assert len(pipe_entries) == 1
    assert pipe_entries[0].name.startswith("Analytics Dashboard")
    assert {"react", "firebase"} == set(pipe_entries[0].technologies)
    assert len(labeled_entries) == 1
    assert labeled_entries[0].name == "Project: Mobile Inventory App"


def test_selective_unicode_cleaning_removes_pdf_zero_width_only():
    assert clean_text("Technical\u200b Skills") == "Technical Skills"
    assert clean_text("A\u200dB") == "A\u200dB"


def test_frontend_jd_required_qualifications_are_separate_from_responsibilities():
    jd_path = (
        Path(__file__).resolve().parents[1]
        / "data/job_descriptions/Job Description - Frontend Developer.pdf"
    )
    jd = parse_job_description(clean_text(extract_text(jd_path)))
    assert "html" in jd.required_skills
    assert "css" in jd.required_skills
    assert "javascript" in jd.required_skills
    assert "react" in jd.required_skills
    assert "git" in jd.required_skills
    assert all(
        "core web technologies" not in responsibility.lower()
        for responsibility in jd.responsibilities
    )
    assert jd.extraction_status["required_skills"] == "extracted"


def test_actual_frontend_resume_extraction_improves_structured_fields():
    repo_root = Path(__file__).resolve().parents[1]
    resume_path = (
        repo_root
        / "data/anonymized_resumes/Ryane Bose - Frontend Developer Resume.pdf"
    )
    resume = parse_resume(
        clean_text(extract_text(resume_path)),
        candidate_id=resume_path.stem,
        source_file=resume_path.name,
    )
    assert "html" in resume.skills
    assert "css" in resume.skills
    assert "javascript" in resume.skills
    assert "git" in resume.skills
    assert len(resume.experience) >= 2
    assert len(resume.projects) >= 1
    assert resume.extraction_status["skills"] == "extracted"
    assert resume.extraction_status["experience"] == "extracted"
    assert resume.extraction_status["projects"] == "extracted"


def test_uniconnect_project_has_no_inferred_technologies():
    repo_root = Path(__file__).resolve().parents[1]
    resume_path = (
        repo_root
        / "data/anonymized_resumes/Ryane Bose - Frontend Developer Resume.pdf"
    )
    resume = parse_resume(
        clean_text(extract_text(resume_path)),
        candidate_id=resume_path.stem,
        source_file=resume_path.name,
    )
    uniconnect = next(
        project
        for project in resume.projects
        if project.name.startswith("UniConnect")
    )
    assert uniconnect.description
    assert uniconnect.technologies == []


def test_extraction_status_enum_is_complete_and_backward_compatible():
    assert {status.value for status in ExtractionStatus} == {
        "missing",
        "empty",
        "extracted",
        "ambiguous",
    }
    assert ExtractionStatus.EXTRACTED == "extracted"
    assert ResumeData(candidate_id="test").extraction_status == {}
    assert JobDescription().extraction_status == {}
