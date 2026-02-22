import uuid
from app.storage.db import create_run, update_run_status
from app.tools import run_tool
from app.generation.concept_generator import generate_concepts
from app.evaluation.evaluator import evaluate_concepts, select_top_n


def run_agent(brand_id, sku_id, channel):
    """Returns dict with run_id and concepts (list of concept dicts)."""
    run_id = str(uuid.uuid4())
    create_run(run_id, brand_id, sku_id, status="running")

    # Load context for generator
    guidelines = run_tool("get_brand_guidelines", brand_id=brand_id)
    past = run_tool("search_past_creatives", brand_id=brand_id, sku_id=sku_id, channel=channel, query="", k=5)
    memory = run_tool("retrieve_memory", brand_id=brand_id, sku_id=sku_id, key="last_run")

    # Generate concepts
    concepts = generate_concepts(brand_id, sku_id, channel, count=10)
    run_tool("log_artifact", run_id=run_id, artifact_type="concepts", payload={"concepts": concepts})

    scored = evaluate_concepts(concepts)
    run_tool("log_artifact", run_id=run_id, artifact_type="evaluation", payload={"scored": scored})
    top_3 = select_top_n(scored, n=3)

    best_concepts = _improve_and_pick_best(top_3)
    _write_run_memory(brand_id, sku_id)

    update_run_status(run_id, "completed")
    return {"run_id": run_id, "concepts": best_concepts}


def _improve_and_pick_best(top_3_scored):
    """(pipeline test; swap for LLM improvement later)."""
    return [item["concept"] for item in top_3_scored]


def _write_run_memory(brand_id, sku_id):
    """stub, will change later."""
    run_tool("write_memory", brand_id=brand_id, sku_id=sku_id, key="last_run", value="Run completed.")
