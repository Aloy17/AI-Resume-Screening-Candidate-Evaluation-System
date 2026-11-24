from src.resume_screening.ranking.ranker import rank_candidates

def test_rank_candidates_and_ties():
    result=rank_candidates([{"filename":"b.pdf","final_score":70},{"filename":"a.pdf","final_score":90},{"filename":"c.pdf","final_score":90}])
    assert [x["rank"] for x in result]==[1,1,3]
    assert [x["filename"] for x in result]==["a.pdf","c.pdf","b.pdf"]
