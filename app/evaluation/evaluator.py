import json
from app.llm import completion

# Heuristic values

HEURISTIC_BASE_SCORE = 5.0
HEURISTIC_HOOK_MIN_LEN = 20
HEURISTIC_BONUS_HOOK_LEN = 1.0
HEURISTIC_BONUS_QUESTION = 0.5
HEURISTIC_PENALTY_COMPLIANCE = 3.0
HEURISTIC_BONUS_SUPPORT = 0.5
DEFAULT_CHANNEL = "paid_social"
DEFAULT_TOP_N = 3

LLM_CRITIC_UNAVAILABLE_MSG = (
    "LLM critic unavailable. Set OPENAI_API_KEY and ensure the API is reachable."
)


def _heuristic_score(concept):
    """Simple heuristic: hook length + compliance (no 'cure'/'treat'). 0-10 scale."""
    hook = (concept.get("hook") or "").strip()
    script = (concept.get("script") or "").lower()
    score = HEURISTIC_BASE_SCORE
    if len(hook) >= HEURISTIC_HOOK_MIN_LEN:
        score += HEURISTIC_BONUS_HOOK_LEN
    if "?" in hook or "why" in hook.lower():
        score += HEURISTIC_BONUS_QUESTION
    if "cure" in script or "treat disease" in script:
        score -= HEURISTIC_PENALTY_COMPLIANCE
    if "support" in script or "help" in script:
        score += HEURISTIC_BONUS_SUPPORT
    return max(0.0, min(10.0, score))


def _llm_critic_score(concept, channel=DEFAULT_CHANNEL):
    """Ask LLM to score concept 0-10. Raises if API key missing or response invalid."""
    hook = concept.get("hook") or ""
    angle = concept.get("angle") or ""
    script = concept.get("script") or ""
    text = completion(
        messages=[
            {
                "role": "system",
                "content": "You are a creative critic for paid social ads. Score the ad concept from 0 to 10. Consider: hook strength (clarity, curiosity), compliance (avoid 'cure'/'treat disease'; prefer 'supports'/'helps'/'promotes'), channel fit, and believability. Reply with valid JSON only: {\"score\": <number 0-10>}",
            },
            {
                "role": "user",
                "content": f"Channel: {channel}\nHook: {hook}\nAngle: {angle}\nScript: {script}",
            },
        ],
        temperature=0.2,
        max_tokens=32,
        response_format={"type": "json_object"},
    )
    if not text:
        raise ValueError(LLM_CRITIC_UNAVAILABLE_MSG)
    try:
        data = json.loads(text)
        s = data.get("score")
        if s is not None:
            return max(0.0, min(10.0, float(s)))
    except (json.JSONDecodeError, TypeError, ValueError):
        pass
    raise ValueError("LLM critic returned invalid JSON or missing 'score'. Check API response.")


def evaluate_concepts(concepts, channel=DEFAULT_CHANNEL):
    """Return list of {concept, heuristic_score, llm_critic_score, score} per concept."""
    evaluated = []
    for concept in concepts:
        h = _heuristic_score(concept)
        llm_critic = _llm_critic_score(concept, channel=concept.get("channel") or channel)
        score = (h + llm_critic) / 2.0
        evaluated.append({
            "concept": concept,
            "heuristic_score": h,
            "llm_critic_score": llm_critic,
            "score": score,
        })
    return evaluated


def select_top_n(scored_list, n=DEFAULT_TOP_N):
    """Sort by combined score descending and return top n."""
    sorted_list = sorted(scored_list, key=lambda x: x["score"], reverse=True)
    return sorted_list[:n]