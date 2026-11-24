
import pytest

from resume_screening.config import Weights, load_weights


@pytest.fixture
def weights_file(tmp_path):
    path = tmp_path / "weights.yaml"
    path.write_text(
        """
default:
  skills: 0.40
  experience: 0.25
  education: 0.15
  projects: 0.20

profiles:
  job_description_python_developer:
    skills: 0.40
    experience: 0.25
    education: 0.10
    projects: 0.25

  job_description_cybersecurity_specialist:
    skills: 0.35
    experience: 0.30
    education: 0.10
    projects: 0.25
""",
        encoding="utf-8",
    )
    return path


def test_load_default_weights(weights_file):
    weights = load_weights(weights_file)

    assert weights == Weights()


def test_load_python_profile(weights_file):
    weights = load_weights(
        weights_file,
        "Job Description - Python Developer.pdf",
    )

    assert weights == Weights(
        skills=0.40,
        experience=0.25,
        education=0.10,
        projects=0.25,
    )


def test_load_cybersecurity_profile(weights_file):
    weights = load_weights(
        weights_file,
        "Job Description - Cybersecurity Specialist.pdf",
    )

    assert weights == Weights(
        skills=0.35,
        experience=0.30,
        education=0.10,
        projects=0.25,
    )


def test_unknown_jd_uses_default(weights_file):
    weights = load_weights(
        weights_file,
        "Unknown_Role.pdf",
    )

    assert weights == Weights()


def test_old_configuration_format(tmp_path):
    path = tmp_path / "old_weights.yaml"
    path.write_text(
        """
weights:
  skills: 0.40
  experience: 0.25
  education: 0.15
  projects: 0.20
""",
        encoding="utf-8",
    )

    assert load_weights(path) == Weights()
