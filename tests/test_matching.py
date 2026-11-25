
import numpy as np

from resume_screening.matching.education import score_education
from resume_screening.matching.experience import score_experience
from resume_screening.matching.projects import score_projects
from resume_screening.matching.skills import _score_skill_group, score_skills
from resume_screening.models import (
    EducationEntry,
    ExperienceEntry,
    JobDescription,
    ProjectEntry,
    ResumeData,
)


class FakeEmbedder:
    def embed(self, texts):
        # Identical vectors make all semantic similarities equal to 1.
        return np.ones((len(texts), 3), dtype=np.float32)


class ZeroSimilarityEmbedder:
    def embed(self, texts):
        return np.zeros((len(texts), 3), dtype=np.float32)


def test_skill_match_does_not_reuse_exact_candidate_skill():
    score = _score_skill_group(
        candidate_skills=["Python"],
        target_skills=["Python", "Python programming"],
        embedder=FakeEmbedder(),
    )

    assert score == 50.0


def test_one_skill_satisfies_an_explicit_alternative_group():
    score = _score_skill_group(
        candidate_skills=["Vue"],
        target_skills=["React", "Vue", "Angular"],
        embedder=ZeroSimilarityEmbedder(),
        alternative_groups=[["React", "Vue", "Angular"]],
    )

    assert score == 100.0


def test_independent_skills_remain_separate_from_alternative_group():
    score = _score_skill_group(
        candidate_skills=["Vue"],
        target_skills=["React", "Vue", "Angular", "Python"],
        embedder=ZeroSimilarityEmbedder(),
        alternative_groups=[["React", "Vue", "Angular"]],
    )

    assert score == 50.0


def test_experience_uses_years_when_responsibilities_are_missing():
    resume = ResumeData(
        candidate_id="candidate-1",
        total_experience_years=5,
        experience=[ExperienceEntry(duration_months=60)],
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
        experience=[ExperienceEntry(duration_months=36)],
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


def test_education_fields_are_matched_and_in_progress_degrees_are_partial():
    completed = ResumeData(
        candidate_id="completed",
        education=[
            EducationEntry(
                degree="Master of Science",
                field_of_study="Computer Science",
            )
        ],
    )
    unrelated = ResumeData(
        candidate_id="unrelated",
        education=[
            EducationEntry(
                degree="Master of Business Administration",
                field_of_study="Business Administration",
            )
        ],
    )
    in_progress = ResumeData(
        candidate_id="in-progress",
        education=[
            EducationEntry(
                degree="Master of Computer Applications",
                field_of_study="Computer Science",
                in_progress=True,
            )
        ],
    )
    jd = JobDescription(
        required_education="Master's degree in Computer Science",
    )

    assert score_education(completed, jd) == 100.0
    assert score_education(unrelated, jd) == 70.0
    assert score_education(in_progress, jd) == 75.0
    assert score_education(
        in_progress,
        JobDescription(
            required_education="Completed Master's degree in Computer Science"
        ),
    ) == 0.0


def test_projects_without_explicit_requirements_use_jd_responsibilities():
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

    score = score_projects(resume, jd, FakeEmbedder())
    assert score == 100.0


def test_projects_without_explicit_requirements_use_jd_skills():
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

    score = score_projects(resume, jd, FakeEmbedder())
    assert score == 100.0


def test_projects_without_explicit_requirements_score_relevance():
    class ProjectRelevanceEmbedder:
        def embed(self, texts):
            vectors = []
            for text in texts:
                if text.startswith("Job requirements:"):
                    vectors.append([1.0, 0.0])
                elif "responsive user interface" in text.lower():
                    vectors.append([0.8, 0.6])
                else:
                    vectors.append([0.0, 1.0])
            return np.asarray(vectors, dtype=np.float32)

    jd = JobDescription(
        required_skills=["React"],
        responsibilities=["Build responsive user interfaces"],
    )
    related = ResumeData(
        candidate_id="related",
        projects=[
            ProjectEntry(
                name="Responsive user interface",
                description="Implemented page components.",
            )
        ],
    )
    unrelated = ResumeData(
        candidate_id="unrelated",
        projects=[
            ProjectEntry(
                name="Unrelated project",
                description="Prepared a garden planting schedule.",
            )
        ],
    )

    related_score = score_projects(related, jd, ProjectRelevanceEmbedder())
    unrelated_score = score_projects(unrelated, jd, ProjectRelevanceEmbedder())

    assert related_score == 80.0
    assert unrelated_score == 0.0


def test_project_count_and_description_length_do_not_inflate_relevance():
    class OrthogonalProjectEmbedder:
        def embed(self, texts):
            vectors = [
                [1.0, 0.0]
                if text.startswith("Job requirements:")
                else [0.0, 1.0]
                for text in texts
            ]
            return np.asarray(vectors, dtype=np.float32)

    jd = JobDescription(responsibilities=["Build a secure API"])
    short_resume = ResumeData(
        candidate_id="short",
        projects=[ProjectEntry(name="Unrelated", description="Gardening.")],
    )
    long_resume = ResumeData(
        candidate_id="long",
        projects=[
            ProjectEntry(
                name=f"Unrelated project {index}",
                description="Gardening and landscape planning. " * 100,
                technologies=["Python", "JavaScript"],
            )
            for index in range(5)
        ],
    )

    assert score_projects(
        short_resume,
        jd,
        OrthogonalProjectEmbedder(),
    ) == 0.0
    assert score_projects(
        long_resume,
        jd,
        OrthogonalProjectEmbedder(),
    ) == 0.0


def test_projects_without_relevant_jd_criteria_use_conservative_zero():
    resume = ResumeData(
        candidate_id="candidate",
        projects=[
            ProjectEntry(
                name="Large project",
                description="Detailed project description. " * 100,
                technologies=["Python", "React", "SQL"],
            )
        ],
    )

    assert score_projects(resume, JobDescription(), FakeEmbedder()) == 0.0


def test_project_technology_tags_alone_do_not_score_fallback():
    resume = ResumeData(
        candidate_id="candidate",
        projects=[
            ProjectEntry(technologies=["Python", "React", "SQL"])
        ],
    )
    jd = JobDescription(
        required_skills=["Python", "React", "SQL"],
        responsibilities=["Build a web application"],
    )

    assert score_projects(resume, jd, FakeEmbedder()) == 0.0


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


def test_project_description_below_similarity_threshold_gets_no_credit():
    class OrthogonalEmbedder:
        def embed(self, texts):
            vectors = []
            for text in texts:
                if text == "Build a backend API":
                    vectors.append([1.0, 0.0, 0.0])
                else:
                    vectors.append([0.0, 1.0, 0.0])
            return np.asarray(vectors, dtype=np.float32)

    score = score_projects(
        ResumeData(
            candidate_id="candidate-1",
            projects=[ProjectEntry(name="Unrelated project", description="An unrelated design project")],
        ),
        JobDescription(project_requirements=["Build a backend API"]),
        OrthogonalEmbedder(),
    )
    assert score == 0.0


def test_responsibility_matching_does_not_reuse_candidate_bullet():
    class OneCandidateBulletEmbedder:
        def embed(self, texts):
            vectors = []
            for text in texts:
                if text == "requirement two":
                    vectors.append([0.0, 1.0, 0.0])
                else:
                    vectors.append([1.0, 0.0, 0.0])
            return np.asarray(vectors, dtype=np.float32)

    resume = ResumeData(
        candidate_id="candidate-1",
        total_experience_years=5,
        experience=[ExperienceEntry(responsibilities=["generic responsibility"])],
    )
    jd = JobDescription(
        min_experience_years=5,
        responsibilities=["requirement one", "requirement two"],
    )
    assert score_experience(resume, jd, OneCandidateBulletEmbedder()) == 85.0


def test_category_missing_requirements_are_not_applicable():
    jd = JobDescription()
    resume = ResumeData(candidate_id="candidate-1")

    assert score_skills(resume, jd, FakeEmbedder()) is None
    assert score_experience(resume, jd, FakeEmbedder()) is None
    assert score_education(resume, jd) is None
    assert score_projects(resume, jd, FakeEmbedder()) == 0.0


def test_required_category_missing_resume_section_scores_zero():
    jd = JobDescription(
        required_skills=["Python"],
        min_experience_years=3,
        required_education="Bachelor",
        project_requirements=["Build a web application"],
    )
    resume = ResumeData(candidate_id="candidate-1")

    assert score_skills(resume, jd, FakeEmbedder()) == 0.0
    assert score_experience(resume, jd, FakeEmbedder()) == 0.0
    assert score_education(resume, jd) == 0.0
    assert score_projects(resume, jd, FakeEmbedder()) == 0.0


def test_required_category_existing_but_unusable_section_does_not_get_100():
    resume = ResumeData(
        candidate_id="candidate-1",
        skills=[],
        experience=[],
        education=[],
        projects=[],
    )
    jd = JobDescription(
        required_skills=["Python"],
        min_experience_years=3,
        required_education="Bachelor",
        project_requirements=["Build a web application"],
    )

    assert score_skills(resume, jd, FakeEmbedder()) == 0.0
    assert score_experience(resume, jd, FakeEmbedder()) == 0.0
    assert score_education(resume, jd) == 0.0
    assert score_projects(resume, jd, FakeEmbedder()) == 0.0


def test_skills_follow_resume_section_applicability():
    from resume_screening.matching.skills import (
        is_skills_applicable,
    )

    jd_with_skills = JobDescription(required_skills=["Python"])
    jd_without_skills = JobDescription()
    empty_resume = ResumeData(candidate_id="candidate-1")
    skilled_resume = ResumeData(
        candidate_id="candidate-1",
        skills=["Python"],
    )

    assert is_skills_applicable(skilled_resume, jd_with_skills)
    assert is_skills_applicable(skilled_resume, jd_without_skills)
    assert is_skills_applicable(empty_resume, jd_with_skills)
    assert not is_skills_applicable(empty_resume, jd_without_skills)

    assert score_skills(empty_resume, jd_with_skills, FakeEmbedder()) == 0.0
    assert score_skills(skilled_resume, jd_without_skills, FakeEmbedder()) == 10.0
    assert score_skills(empty_resume, jd_without_skills, FakeEmbedder()) is None


def test_experience_follows_resume_section_applicability():
    from resume_screening.matching.experience import (
        is_experience_applicable,
    )

    jd_with_criteria = JobDescription(min_experience_years=3)
    jd_without_criteria = JobDescription()
    empty_resume = ResumeData(candidate_id="candidate-1")
    experienced_resume = ResumeData(
        candidate_id="candidate-1",
        experience=[ExperienceEntry(
            duration_months=36,
            responsibilities=["Built an application"],
        )],
        total_experience_years=3.0,
    )

    assert is_experience_applicable(experienced_resume, jd_with_criteria)
    assert is_experience_applicable(experienced_resume, jd_without_criteria)
    assert is_experience_applicable(empty_resume, jd_with_criteria)
    assert not is_experience_applicable(empty_resume, jd_without_criteria)

    assert score_experience(empty_resume, jd_with_criteria, FakeEmbedder()) == 0.0
    assert score_experience(
        experienced_resume,
        jd_with_criteria,
        FakeEmbedder(),
    ) == 100.0
    assert 0.0 < score_experience(
        experienced_resume,
        jd_without_criteria,
        FakeEmbedder(),
    ) < 100.0
    assert score_experience(
        empty_resume,
        jd_without_criteria,
        FakeEmbedder(),
    ) is None


def test_education_applicability_depends_only_on_jd():
    from resume_screening.matching.education import (
        is_education_applicable,
    )

    resume_with_education = ResumeData(
        candidate_id="candidate-1",
        education=[EducationEntry(degree="Bachelor")],
    )
    resume_without_education = ResumeData(candidate_id="candidate-1")
    jd_with_education = JobDescription(required_education="Bachelor")
    jd_without_education = JobDescription()

    assert is_education_applicable(jd_with_education)
    assert not is_education_applicable(jd_without_education)
    assert score_education(resume_with_education, jd_without_education) is None
    assert score_education(resume_without_education, jd_with_education) == 0.0


def test_projects_are_always_applicable_and_missing_resume_section_scores_zero():
    from resume_screening.matching.projects import (
        is_projects_applicable,
    )

    jd = JobDescription(required_skills=["Python"])
    resume_with_projects = ResumeData(
        candidate_id="candidate-1",
        projects=[ProjectEntry(
            name="Portfolio",
            description="A detailed personal portfolio with responsive sections.",
            technologies=["HTML"],
        )],
    )
    resume_without_projects = ResumeData(candidate_id="candidate-1")

    assert is_projects_applicable(jd)
    assert score_projects(resume_without_projects, jd, FakeEmbedder()) == 0.0
    assert 0.0 < score_projects(
        resume_with_projects,
        jd,
        FakeEmbedder(),
    ) <= 100.0
