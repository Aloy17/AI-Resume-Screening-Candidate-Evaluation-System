from resume_screening.models import CandidateResult, CategoryScores
from resume_screening.ranking import rank_candidates


def make(cid, final, skills=0.0):
    return CandidateResult(
        candidate_id=cid,
        source_file=f"{cid}.pdf",
        scores=CategoryScores(skills=skills),
        final_score=final,
    )


def test_sorted_high_to_low_with_ranks():
    ranked = rank_candidates([make("a", 50), make("b", 90), make("c", 70)])
    assert [r.candidate_id for r in ranked] == ["b", "c", "a"]
    assert [r.rank for r in ranked] == [1, 2, 3]


def test_tie_broken_by_skills_then_id():
    ranked = rank_candidates(
        [make("z", 80, skills=60), make("a", 80, skills=60), make("m", 80, skills=90)]
    )
    assert [r.candidate_id for r in ranked] == ["m", "a", "z"]


def test_empty_list():
    assert rank_candidates([]) == []


def test_to_dict_includes_category_scores():
    d = rank_candidates([make("a", 61.234, skills=70)])[0].to_dict()
    assert d["rank"] == 1
    assert d["final_score"] == 61.23
    assert d["scores"]["skills"] == 70
