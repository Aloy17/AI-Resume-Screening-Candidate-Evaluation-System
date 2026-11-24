"""Stage 7: Sort candidates from highest to lowest final score and assign ranks."""

from __future__ import annotations

from ..models import CandidateResult


def rank_candidates(results: list[CandidateResult]) -> list[CandidateResult]:
    """Return results sorted best first with ranks 1..n.

    Ties on final score are broken by skills score, then by candidate id, so output is deterministic.
    """
    ordered = sorted(
        results,
        key=lambda r: (-r.final_score, -r.scores.skills, r.candidate_id),
    )
    for position, result in enumerate(ordered, start=1):
        result.rank = position
    return ordered
