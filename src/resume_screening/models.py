"""Data models shared across the pipeline.

All scores are on a 0 to 100 scale.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


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


@dataclass
class CategoryScores:
    skills: float = 0.0
    experience: float = 0.0
    education: float = 0.0
    projects: float = 0.0

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


@dataclass
class CandidateResult:
    candidate_id: str
    source_file: str
    scores: CategoryScores
    final_score: float = 0.0
    rank: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "candidate_id": self.candidate_id,
            "source_file": self.source_file,
            "final_score": round(self.final_score, 2),
            "scores": {k: round(v, 2) for k, v in self.scores.to_dict().items()},
        }
