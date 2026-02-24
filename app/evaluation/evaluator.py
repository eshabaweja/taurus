import json
from app.llm import completion

# Heuristic values

HEURISTIC_BASE_SCORE = 5.0
HEURISTIC_HOOK_MIN_LEN = 20
HEURISTIC_BONUS_HOOK_LEN = 1.0
HEURISTIC_BONUS_QUESTION = 0.5
DEFAULT_CHANNEL = "paid_social"
DEFAULT_TOP_N = 3

LLM_CRITIC_UNAVAILABLE_MSG = (
    "LLM critic unavailable. Set OPENAI_API_KEY and ensure the API is reachable."
)


def _heuristic_score(concept):
    """Simple heuristic: hook length and question-style only. 0-10 scale. Compliance is left to context/guidelines."""
    hook = (concept.get("hook") or "").strip()
    score = HEURISTIC_BASE_SCORE
    if len(hook) >= HEURISTIC_HOOK_MIN_LEN:
        score += HEURISTIC_BONUS_HOOK_LEN
    if "?" in hook or "why" in hook.lower():
        score += HEURISTIC_BONUS_QUESTION
    return max(0.0, min(10.0, score))


def _llm_critic_score(concept, channel=DEFAULT_CHANNEL, guidelines=None):
    """Ask LLM to score concept 0-10. Raises if API key missing or response invalid."""
    hook = concept.get("hook") or ""
    angle = concept.get("angle") or ""
    script = concept.get("script") or ""
    user_content = f"Channel: {channel}\nHook: {hook}\nAngle: {angle}\nScript: {script}"
    if guidelines:
        user_content = f"Brand guidelines (assess compliance with do's and don'ts):\n{json.dumps(guidelines, indent=2)}\n\n{user_content}"
    text = completion(
        messages=[
            {
                "role": "system",
                "content": "You are a creative critic for paid social ads. Score the ad concept from 0 to 10. Consider: hook strength (clarity, curiosity), compliance with brand guidelines when provided in context, channel fit, and believability. Reply with valid JSON only: {\"score\": <number 0-10>}",
            },
            {
                "role": "user",
                "content": user_content,
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


def evaluate_concepts(concepts, channel=DEFAULT_CHANNEL, guidelines=None):
    """Return list of {concept, heuristic_score, llm_critic_score, score} per concept."""
    evaluated = []
    for concept in concepts:
        h = _heuristic_score(concept)
        llm_critic = _llm_critic_score(concept, channel=concept.get("channel") or channel, guidelines=guidelines)
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