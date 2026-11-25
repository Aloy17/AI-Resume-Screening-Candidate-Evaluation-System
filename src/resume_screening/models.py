"""Data models shared across the pipeline.

All scores are on a 0 to 100 scale.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class ExtractionStatus(str, Enum):
    """Supported structured parsing states."""

    MISSING = "missing"
    EMPTY = "empty"
    EXTRACTED = "extracted"
    AMBIGUOUS = "ambiguous"


class CategoryStatus(str, Enum):
    """Whether a category is applicable to a candidate/JD evaluation."""

    APPLICABLE = "applicable"
    NOT_APPLICABLE = "not_applicable"


@dataclass
class ExperienceEntry:
    title: str = ""
    company: str = ""
    duration_months: float | None = None
    responsibilities: list[str] = field(default_factory=list)


@dataclass
class EducationEntry:
    degree: str = ""
    field_of_study: str = ""
    institution: str = ""
    year: int | None = None


@dataclass
class ProjectEntry:
    name: str = ""
    description: str = ""
    technologies: list[str] = field(default_factory=list)


@dataclass
class ResumeData:
    """Structured JSON form of a parsed resume."""

    candidate_id: str
    source_file: str = ""
    skills: list[str] = field(default_factory=list)
    experience: list[ExperienceEntry] = field(default_factory=list)
    education: list[EducationEntry] = field(default_factory=list)
    projects: list[ProjectEntry] = field(default_factory=list)
    total_experience_years: float = 0.0
    extraction_status: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)



@dataclass
class JobDescription:
    """Structured JSON form of a parsed job description."""

    title: str = ""

    # Skills
    required_skills: list[str] = field(default_factory=list)
    preferred_skills: list[str] = field(default_factory=list)

    # Experience
    min_experience_years: float = 0.0
    max_experience_years: float | None = None

    # Education
    required_education: str = ""
    preferred_education: str = ""

    # Job requirements
    responsibilities: list[str] = field(default_factory=list)
    project_requirements: list[str] = field(default_factory=list)

    # Certifications
    required_certifications: list[str] = field(default_factory=list)
    preferred_certifications: list[str] = field(default_factory=list)

    # Recruiter evaluation priorities
    evaluation_emphasis: list[str] = field(default_factory=list)

    # Original extracted text
    raw_text: str = ""

    # Whether each structured field was absent, empty, extracted, or ambiguous.
    extraction_status: dict[str, str] = field(default_factory=dict)


@dataclass
class CategoryScores:
    skills: float | None = 0.0
    experience: float | None = 0.0
    education: float | None = 0.0
    projects: float | None = 0.0
    applicability: dict[str, CategoryStatus] = field(default_factory=dict)

    def to_dict(self) -> dict[str, float | None]:
        return {
            "skills": None if self.skills is None else round(self.skills, 2),
            "experience": None if self.experience is None else round(self.experience, 2),
            "education": None if self.education is None else round(self.education, 2),
            "projects": None if self.projects is None else round(self.projects, 2),
        }

    def applicability_dict(self) -> dict[str, str]:
        return {
            category: (
                status.value
                if isinstance(status, CategoryStatus)
                else str(status)
            )
            for category, status in self.applicability.items()
        }


@dataclass
class CandidateResult:
    candidate_id: str
    source_file: str
    scores: CategoryScores
    final_score: float | None = 0.0
    rank: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "candidate_id": self.candidate_id,
            "source_file": self.source_file,
            "final_score": (
                None
                if self.final_score is None
                else round(self.final_score, 2)
            ),
            "scores": self.scores.to_dict(),
            "applicability": self.scores.applicability_dict(),
        }
