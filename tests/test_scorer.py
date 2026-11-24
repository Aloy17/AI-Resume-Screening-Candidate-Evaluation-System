import pytest
from src.resume_screening.scoring.scorer import calculate_final_score,determine_weights

def test_weighted_score_uses_all_categories():
    scores={"skills":100,"experience":80,"education":60,"projects":40,"certifications":20}
    weights={k:.2 for k in scores}
    assert calculate_final_score(scores,weights)["final_score"]==60

def test_missing_category_weights_are_renormalized():
    scores={"skills":100,"experience":0,"education":None,"projects":None,"certifications":None}
    weights={"skills":.5,"experience":.5,"education":0,"projects":0,"certifications":0}
    result=calculate_final_score(scores,weights)
    assert result["final_score"]==50
    assert result["excluded_categories"]==["education","projects","certifications"]

def test_invalid_weights_rejected():
    with pytest.raises(ValueError):
        calculate_final_score({"skills":1},{"skills":1})

def test_role_profiles():
    assert determine_weights({"job_title":"DevOps Engineer"})["certifications"]>.2
    assert determine_weights({"job_title":"Python Developer"})["projects"]>.2
