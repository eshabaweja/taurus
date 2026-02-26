import json
import os
import uuid
from app.storage.db import create_run, update_run_status, create_top_creatives
from app.tools import run_tool
from app.generation.concept_generator import generate_concepts
from app.evaluation.evaluator import evaluate_concepts, select_top_n, DEFAULT_TOP_N
from app.llm import completion
from app.vector_store import index_top_creatives, query_top_creatives_for_generation, index_memory_learnings, query_memory_learnings


CONCEPTS_PER_RUN = int(os.environ.get("CONCEPTS_PER_RUN", "10"))
MEMORY_KEY_LAST_RUN = os.environ.get("MEMORY_KEY_LAST_RUN", "last_run")
PAST_CREATIVES_K = int(os.environ.get("PAST_CREATIVES_K", "5"))
PAST_CREATIVES_QUERY_DEFAULT = os.environ.get("PAST_CREATIVES_QUERY_DEFAULT", "")
# Used so agent and evaluator stay in sync
TOP_N = int(os.environ.get("TOP_N", str(DEFAULT_TOP_N)))


def run_agent(brand_id, sku_id, channel):
    """Returns dict with run_id and concepts (list of concept dicts)."""
    run_id = str(uuid.uuid4())
    create_run(run_id, brand_id, sku_id, status="running")

    # Load context for generator
    guidelines = run_tool("get_brand_guidelines", brand_id=brand_id)
    past = run_tool(
        "search_past_creatives",
        brand_id=brand_id,
        sku_id=sku_id,
        channel=channel,
        query=PAST_CREATIVES_QUERY_DEFAULT,
        k=PAST_CREATIVES_K,
    )
    memory = run_tool("retrieve_memory", brand_id=brand_id, sku_id=sku_id, key=MEMORY_KEY_LAST_RUN)

    # Retrieve top-performing concepts from vector memory (if any) to use as extra context
    top_creatives_context = None
    try:
        vec_results = query_top_creatives_for_generation(brand_id, sku_id, channel, k=5)
        docs = (vec_results.get("documents") or [[]])[0]
        metas = (vec_results.get("metadatas") or [[]])[0]
        lines = []
        for doc, meta in zip(docs, metas):
            hook = (meta or {}).get("hook") or (doc or "")[:120]
            angle = (meta or {}).get("angle") or ""
            score = (meta or {}).get("score")
            parts = [f"Hook: {hook}"]
            if angle:
                parts.append(f"Angle: {angle}")
            if isinstance(score, (int, float)):
                parts.append(f"Score: {score:.1f}")
            lines.append(" | ".join(parts))
        if lines:
            top_creatives_context = "\n".join(f"- {line}" for line in lines)
    except Exception:
        top_creatives_context = None

    # Retrieve distilled learnings from vector memory (if any)
    vector_learnings_context = None
    try:
        vec_learnings = query_memory_learnings(brand_id, sku_id, k=5)
        if vec_learnings:
            vector_learnings_context = "\n".join(f"- {s}" for s in vec_learnings)
    except Exception:
        vector_learnings_context = None

    # Generate concepts (LLM uses guidelines, past, memory, and vector memory when available)
    concepts = generate_concepts(
        brand_id, sku_id, channel, count=CONCEPTS_PER_RUN,
        guidelines=guidelines, past=past, memory=memory,
        top_creatives=top_creatives_context,
        vector_learnings=vector_learnings_context,
    )
    run_tool("log_artifact", run_id=run_id, artifact_type="concepts", payload={"concepts": concepts})

    scored = evaluate_concepts(concepts, brand_id=brand_id, sku_id=sku_id, channel=channel, guidelines=guidelines,)
    run_tool("log_artifact", run_id=run_id, artifact_type="evaluation", payload={"scored": scored})
    top_3 = select_top_n(scored, n=TOP_N)

    best_concepts = _improve_and_pick_best(top_3, channel, brand_id, sku_id, guidelines=guidelines)

    winners_scored = evaluate_concepts(best_concepts, brand_id=brand_id, sku_id=sku_id, channel=channel,guidelines=guidelines,)
    create_top_creatives(run_id, brand_id, sku_id, channel, winners_scored)

    # Also index winners into the vector store so they can be retrieved by future runs.
    creatives_for_index = []
    for rank, item in enumerate(winners_scored, start=1):
        concept = item.get("concept") or {}
        creatives_for_index.append(
            {
                "run_id": run_id,
                "brand_id": brand_id,
                "sku_id": sku_id,
                "channel": concept.get("channel") or channel,
                "rank": rank,
                "score": item.get("score", 0.0),
                "hook": concept.get("hook") or "",
                "angle": concept.get("angle") or "",
                "script": concept.get("script") or "",
            }
        )
    if creatives_for_index:
        try:
            index_top_creatives(creatives_for_index)
        except Exception:
            pass
    _write_run_memory(brand_id, sku_id, top_3_scored=top_3, best_concepts=best_concepts)

    update_run_status(run_id, "completed")
    return {"run_id": run_id, "concepts": best_concepts}


def _generate_improved_variants(concept, channel, feedback_text, brand_id, sku_id, guidelines=None, count=2):
    """Ask LLM for `count` improved variants of the concept. Returns list of concept dicts or []."""
    hook = concept.get("hook") or ""
    angle = concept.get("angle") or ""
    script = concept.get("script") or ""
    shot_list = concept.get("shot_list") or ""
    cta = concept.get("cta") or ""
    context = f"Concept:\nHook: {hook}\nAngle: {angle}\nScript: {script}\nShot list: {shot_list}\nCTA: {cta}\n\nFeedback: {feedback_text}\n\nChannel: {channel}."
    if guidelines:
        context = f"Brand guidelines (follow do's and don'ts):\n{json.dumps(guidelines, indent=2)}\n\n{context}"
    text = completion(
        messages=[
            {
                "role": "system",
                "content": "You are a creative optimizer for paid social ads. Given an ad concept and brief feedback, output exactly 2 improved variants as a JSON array. Each object must have: creative_id, sku_id, channel, hook, angle, script, shot_list, cta. Follow the brand's guidelines from the context when provided. Reply with only the JSON array, no markdown.",
            },
            {
                "role": "user",
                "content": context + "\n\nOutput 2 improved variants as JSON array:",
            },
        ],
        max_tokens=1024,
        temperature=0.6,
    )
    if not text:
        return []
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
            return []
        out = []
        for i, item in enumerate(raw[:count]):
            if not isinstance(item, dict):
                continue
            c = {
                "creative_id": str(item.get("creative_id", f"{brand_id}-imp-{i+1}")),
                "sku_id": str(item.get("sku_id", sku_id)),
                "channel": str(item.get("channel", channel)),
                "hook": str(item.get("hook", "")) or hook,
                "angle": str(item.get("angle", "")) or angle,
                "script": str(item.get("script", "")) or script,
                "shot_list": str(item.get("shot_list", "")) or shot_list,
                "cta": str(item.get("cta", "")) or cta,
            }
            out.append(c)
        return out
    except (json.JSONDecodeError, TypeError):
        return []


def _improve_and_pick_best(top_3_scored, channel, brand_id, sku_id, guidelines=None):
    """For each top concept: generate 2 improved variants, re-score, return the best per slot."""
    best = []
    for item in top_3_scored:
        concept = item["concept"]
        h = item.get("heuristic_score", 0)
        llm_s = item.get("llm_critic_score", 0)
        feedback_text = f"Heuristic score {h:.1f}, critic score {llm_s:.1f}. Improve hook strength and compliance with brand guidelines."
        variants = _generate_improved_variants(
            concept, channel, feedback_text, brand_id, sku_id, guidelines=guidelines, count=2
        )
        candidates = [concept]
        candidates.extend(variants)
        scored = evaluate_concepts(candidates, brand_id=brand_id, sku_id=sku_id,channel=channel,guidelines=guidelines,)
        winner = max(scored, key=lambda x: x["score"])
        best.append(winner["concept"])
    return best


def _distill_learnings(top_3_scored, best_concepts):
    """Derive 1-3 short learnings from top scored concepts and final best concepts."""
    learnings = []
    # Hook patterns: question-style hooks in winners
    hooks = [c.get("hook") or "" for c in best_concepts]
    if any("?" in h or "why" in h.lower() or "what" in h.lower() for h in hooks):
        learnings.append("Question-style hooks (e.g. 'Why...', 'What if...') performed well.")
    # Script compliance: refer to context/guidelines
    scripts = [c.get("script") or "" for c in best_concepts]
    if scripts:
        learnings.append("Scripts aligned with brand guidelines from context.")
    # Scores summary
    if top_3_scored:
        avg = sum(s.get("score", 0) for s in top_3_scored) / len(top_3_scored)
        learnings.append(f"Top concepts averaged score {avg:.1f}; aim for clarity and compliance.")
    if not learnings:
        learnings.append("Run completed; refine based on performance.")
    return learnings


def _write_run_memory(brand_id, sku_id, top_3_scored=None, best_concepts=None):
    """Persist distilled learnings from this run so the next run can use them."""
    top_3_scored = top_3_scored or []
    best_concepts = best_concepts or []
    learnings = _distill_learnings(top_3_scored, best_concepts)
    value = json.dumps(learnings)
    run_tool("write_memory", brand_id=brand_id, sku_id=sku_id, key=MEMORY_KEY_LAST_RUN, value=value)

    # index learnings into vector memory
    try:
        index_memory_learnings(brand_id, sku_id, MEMORY_KEY_LAST_RUN, learnings)
    except Exception:
        pass
