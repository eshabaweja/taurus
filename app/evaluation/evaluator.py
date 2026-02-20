def _heuristic_score(concept):
    """Simple heuristic: hook length + compliance (no 'cure'/'treat'). 0-10 scale."""
    hook = (concept.get("hook") or "").strip()
    script = (concept.get("script") or "").lower()
    score = 5.0
    if len(hook) >= 20:
        score += 1.0
    if "?" in hook or "why" in hook.lower():
        score += 0.5
    if "cure" in script or "treat disease" in script:
        score -= 3.0
    if "support" in script or "help" in script:
        score += 0.5
    return max(0.0, min(10.0, score))


def evaluate_concepts(concepts):
    """Return list of {concept, heuristic_score, llm_critic_score, score} per concept."""
    evaluated = []
    for concept in concepts:
        h = _heuristic_score(concept)
        # Stub: real LLM critic later
        llm_critic = 7.0
        score = (h + llm_critic) / 2.0
        evaluated.append({
            "concept": concept,
            "heuristic_score": h,
            "llm_critic_score": llm_critic,
            "score": score,
        })
    return evaluated


def select_top_n(scored_list, n=3):
    """Sort by combined score descending and return top n."""
    sorted_list = sorted(scored_list, key=lambda x: x["score"], reverse=True)
    return sorted_list[:n]