import json
from app.llm import completion

# Default when callers do not pass count
DEFAULT_CONCEPT_COUNT = 10


def _generate_concepts_llm(
    brand_id,
    sku_id,
    channel,
    count,
    guidelines=None,
    past=None,
    memory=None,
    top_creatives=None,
):
    """Call LLM to generate `count` concepts. Returns list of concept dicts or None on failure."""
    context_parts = []
    if guidelines:
        context_parts.append("Brand guidelines:\n" + json.dumps(guidelines, indent=2))
    if past:
        context_parts.append("Past creatives (top examples):\n" + json.dumps(past[:5], indent=2))
    if memory:
        context_parts.append("Previous learnings:\n" + json.dumps(memory, indent=2))
    if top_creatives:
        context_parts.append("Top-performing past concepts:\n" + str(top_creatives))
    context = "\n\n".join(context_parts) if context_parts else "No extra context."

    system = """You are a creative strategist for paid social ads. Generate ad concepts as a JSON array.
Each object must have: "hook", "angle", "script", "shot_list", "cta".
- hook: attention-grabbing headline (short, curiosity or question)
- angle: one-line value proposition
- script: 1-2 sentences; follow the brand's do's and don'ts from the guidelines when provided in context
- shot_list: 2-4 shot descriptions
- cta: single call-to-action
Return only the JSON array, no markdown or explanation."""

    user = f"""Brand: {brand_id}, SKU: {sku_id}, Channel: {channel}. Generate exactly {count} concepts.

{context}

Output a JSON array of {count} concept objects with keys: hook, angle, script, shot_list, cta."""

    text = completion(
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        max_tokens=4096,
        temperature=0.8,
    )
    if not text:
        return None
    # Strip markdown code block if present
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    try:
        raw = json.loads(text)
        if not isinstance(raw, list):
            return None
        out = []
        for i, item in enumerate(raw[:count]):
            if not isinstance(item, dict):
                continue
            c = {
                "creative_id": f"{brand_id}-gen-{i+1}",
                "sku_id": sku_id,
                "channel": channel,
                "hook": str(item.get("hook", "")) or "Hook",
                "angle": str(item.get("angle", "")) or "Angle",
                "script": str(item.get("script", "")) or "Script",
                "shot_list": str(item.get("shot_list", "")) or "Shot list",
                "cta": str(item.get("cta", "")) or "CTA",
            }
            out.append(c)
        return out if out else None
    except (json.JSONDecodeError, TypeError):
        return None


def generate_concepts(
    brand_id,
    sku_id,
    channel,
    count=None,
    guidelines=None,
    past=None,
    memory=None,
    top_creatives=None,
):
    """Return concepts from LLM. Returns empty list if OPENAI_API_KEY unset or generation fails."""
    if count is None:
        count = DEFAULT_CONCEPT_COUNT
    concepts = _generate_concepts_llm(
        brand_id,
        sku_id,
        channel,
        count,
        guidelines=guidelines,
        past=past,
        memory=memory,
        top_creatives=top_creatives,
    )
    return concepts if concepts else []
