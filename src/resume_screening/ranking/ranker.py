"""Stage 7: Sort candidates from highest to lowest final score and assign ranks."""

from __future__ import annotations

from ..models import CandidateResult


def rank_candidates(results: list[CandidateResult]) -> list[CandidateResult]:
    """Return results sorted best first with ranks 1..n.

    Ties on final score are broken by skills score, then by candidate id, so output is deterministic.
    """
    def sort_key(result: CandidateResult) -> tuple:
        if result.final_score is None:
            return (1, 0.0, 0.0, result.candidate_id)

        skills = result.scores.skills
        if skills is None:
            skills = 0.0

        return (
            0,
            -result.final_score,
            -skills,
            result.candidate_id,
        )

    ordered = sorted(results, key=sort_key)
    for position, result in enumerate(ordered, start=1):
        result.rank = position
    return ordered
