import pytest

from resume_screening.config import Weights
from resume_screening.models import CategoryScores
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
