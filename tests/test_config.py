import pytest

from resume_screening.config import Weights, load_weights


def test_default_weights_sum_to_one():
    w = Weights()
    assert w.skills + w.experience + w.education + w.projects == pytest.approx(1.0)


def test_weights_must_sum_to_one():
    with pytest.raises(ValueError):
        Weights(skills=0.5, experience=0.5, education=0.5, projects=0.5)


def test_weights_must_be_non_negative():
    with pytest.raises(ValueError):
        Weights(skills=1.2, experience=-0.2, education=0.0, projects=0.0)


def test_load_weights_from_yaml(tmp_path):
    f = tmp_path / "w.yaml"
    f.write_text("weights:\n  skills: 0.5\n  experience: 0.2\n  education: 0.1\n  projects: 0.2\n")
    w = load_weights(f)
    assert w.skills == 0.5
    assert w.projects == 0.2


def test_load_weights_rejects_unknown_category(tmp_path):
    f = tmp_path / "w.yaml"
    f.write_text("weights:\n  skills: 0.4\n  luck: 0.6\n")
    with pytest.raises(ValueError):
        load_weights(f)


def test_load_weights_missing_file_uses_defaults(tmp_path):
    assert load_weights(tmp_path / "nope.yaml") == Weights()


def test_repo_weights_file_is_valid():
    w = load_weights("config/weights.yaml")
    assert (w.skills, w.experience, w.education, w.projects) == (0.40, 0.25, 0.15, 0.20)
