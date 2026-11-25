from resume_screening.models import (
    CandidateResult,
    CategoryScores,
    CategoryStatus,
)
from resume_screening.ranking import rank_candidates
from resume_screening.cli import display_ranking


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


def test_unavailable_final_score_is_ranked_last_deterministically():
    unavailable_one = CandidateResult(
        candidate_id="z",
        source_file="z.pdf",
        scores=CategoryScores(applicability={
            "skills": CategoryStatus.NOT_APPLICABLE,
        }),
        final_score=None,
    )
    unavailable_two = CandidateResult(
        candidate_id="a",
        source_file="a.pdf",
        scores=CategoryScores(),
        final_score=None,
    )
    ranked = rank_candidates([
        make("b", 50),
        unavailable_one,
        unavailable_two,
    ])
    assert [result.candidate_id for result in ranked] == ["b", "a", "z"]


def test_cli_displays_na_for_unavailable_category(capsys):
    result = CandidateResult(
        candidate_id="no-applicable-categories",
        source_file="none.pdf",
        scores=CategoryScores(
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
        ),
        final_score=None,
        rank=1,
    )

    display_ranking([result])
    output = capsys.readouterr().out
    assert "N/A" in output
    assert "0.00" not in output
