
import numpy as np

from resume_screening.matching.education import score_education
from resume_screening.matching.experience import score_experience
from resume_screening.matching.projects import score_projects
from resume_screening.matching.skills import _score_skill_group
from resume_screening.models import (
    EducationEntry,
    JobDescription,
    ProjectEntry,
    ResumeData,
)


class FakeEmbedder:
    def embed(self, texts):
        # Identical vectors make all semantic similarities equal to 1.
        return np.ones((len(texts), 3), dtype=np.float32)


def test_skill_match_does_not_reuse_exact_candidate_skill():
    score = _score_skill_group(
        candidate_skills=["Python"],
        target_skills=["Python", "Python programming"],
        embedder=FakeEmbedder(),
    )

    assert score == 50.0


def test_experience_uses_years_when_responsibilities_are_missing():
    resume = ResumeData(
        candidate_id="candidate-1",
        total_experience_years=5,
    )
    jd = JobDescription(
        min_experience_years=5,
        responsibilities=["Build backend services"],
    )

    assert score_experience(resume, jd, FakeEmbedder()) == 100.0


def test_experience_uses_years_when_jd_has_no_responsibilities():
    resume = ResumeData(
        candidate_id="candidate-1",
        total_experience_years=3,
    )
    jd = JobDescription(min_experience_years=5)

    assert score_experience(resume, jd, FakeEmbedder()) == 60.0


def test_education_recognizes_mca_and_computer_applications():
    resume = ResumeData(
        candidate_id="candidate-1",
        education=[
            EducationEntry(
                degree="MCA",
                field_of_study="Computer Applications",
                institution="Example University",
            )
        ],
    )
    jd = JobDescription(
        required_education="MCA in Computer Applications",
    )

    assert score_education(resume, jd) == 100.0


def test_projects_do_not_use_general_responsibilities_as_requirements():
    resume = ResumeData(
        candidate_id="candidate-1",
        projects=[
            ProjectEntry(
                name="Portfolio Website",
                description="A personal portfolio",
                technologies=["HTML", "CSS"],
            )
        ],
    )
    jd = JobDescription(
        responsibilities=["Build scalable backend services"],
    )

    assert score_projects(resume, jd, FakeEmbedder()) == 0.0


def test_projects_can_be_scored_using_technology_overlap_alone():
    resume = ResumeData(
        candidate_id="candidate-1",
        projects=[
            ProjectEntry(
                name="Python API",
                description="A backend API",
                technologies=["Python", "FastAPI"],
            )
        ],
    )
    jd = JobDescription(
        required_skills=["Python", "FastAPI"],
    )

    assert score_projects(resume, jd, FakeEmbedder()) == 100.0


def test_one_project_cannot_fulfil_multiple_project_requirements():
    resume = ResumeData(
        candidate_id="candidate-1",
        projects=[
            ProjectEntry(
                name="Backend API",
                description="A backend API project",
            )
        ],
    )
    jd = JobDescription(
        project_requirements=[
            "Build a backend API",
            "Build a mobile application",
        ],
    )

    assert score_projects(resume, jd, FakeEmbedder()) == 50.0
