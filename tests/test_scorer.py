import pytest

from resume_screening.config import Weights
from resume_screening.models import CategoryScores, CategoryStatus
from resume_screening.scoring import compute_final_score


def test_weighted_sum_with_default_weights():
    scores = CategoryScores(skills=100, experience=50, education=0, projects=100)
    # 100*0.40 + 50*0.25 + 0*0.15 + 100*0.20
    assert compute_final_score(scores, Weights()) == pytest.approx(72.5)


def test_all_zero_scores():
    assert compute_final_score(CategoryScores(), Weights()) == 0.0


def test_perfect_scores_give_100():
    scores = CategoryScores(skills=100, experience=100, education=100, projects=100)
    assert compute_final_score(scores, Weights()) == pytest.approx(100.0)


def test_custom_weights_change_result():
    scores = CategoryScores(skills=100, experience=0, education=0, projects=0)
    w = Weights(skills=0.7, experience=0.1, education=0.1, projects=0.1)
    assert compute_final_score(scores, w) == pytest.approx(70.0)


def test_na_category_weight_is_redistributed():
    scores = CategoryScores(
        skills=100,
        experience=50,
        education=None,
        projects=100,
        applicability={
            "skills": CategoryStatus.APPLICABLE,
            "experience": CategoryStatus.APPLICABLE,
            "education": CategoryStatus.NOT_APPLICABLE,
            "projects": CategoryStatus.APPLICABLE,
        },
    )
    # 40/85 for skills, 25/85 for experience, 20/85 for projects.
    assert compute_final_score(scores, Weights()) == pytest.approx(
        100 * (40 / 85)
        + 50 * (25 / 85)
        + 100 * (20 / 85),
        abs=0.01,
    )


def test_missing_required_category_reuses_its_original_weight_as_zero():
    scores = CategoryScores(
        skills=100,
        experience=0,
        education=None,
        projects=100,
        applicability={
            "skills": CategoryStatus.APPLICABLE,
            "experience": CategoryStatus.APPLICABLE,
            "education": CategoryStatus.NOT_APPLICABLE,
            "projects": CategoryStatus.APPLICABLE,
        },
    )
    # Education is N/A, so applicable weights 40/85, 25/85, and 20/85.
    # Experience remains applicable with 25/85 and contributes zero.
    assert compute_final_score(scores, Weights()) == pytest.approx(
        100 * (40 / 85) + 0 * (25 / 85) + 100 * (20 / 85),
        abs=0.01,
    )


def test_all_categories_na_returns_unavailable():
    scores = CategoryScores(
        skills=None,
        experience=None,
        education=None,
        projects=None,
        applicability={
            "skills": CategoryStatus.NOT_APPLICABLE,
            "experience": CategoryStatus.NOT_APPLICABLE,
            "education": CategoryStatus.NOT_APPLICABLE,
            "projects": CategoryStatus.NOT_APPLICABLE,
        },
    )
    assert compute_final_score(scores, Weights()) is None
