"""Deterministic candidate ranking."""
def rank_candidates(results: list[dict]) -> list[dict]:
    """Sort by final score descending; ties share the same competition rank."""
    ordered = sorted(results, key=lambda item: (-float(item["final_score"]), str(item.get("filename", "")).casefold()))
    ranked, previous_score, current_rank = [], None, 0
    for position, item in enumerate(ordered, start=1):
        score = round(float(item["final_score"]), 2)
        if score != previous_score:
            current_rank = position
        ranked.append({**item, "rank": current_rank})
        previous_score = score
    return ranked
