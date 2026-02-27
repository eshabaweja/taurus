import chromadb

_client = None


def get_client():
    """Return a persistent Chroma client shared across the process."""
    global _client
    if _client is None:
        # to reuse memory across runs
        _client = chromadb.PersistentClient(path=".chromadb")
    return _client

def get_collection(name: str):
    client = get_client()
    return client.get_or_create_collection(name=name)

def index_top_creatives(creatives: list[dict]):
    coll = get_collection("top_creatives")
    documents = [f"{c['hook']} {c['angle']} {c['script']}" for c in creatives]
    metadatas = [
        {
            "run_id": c["run_id"],
            "brand_id": c["brand_id"],
            "sku_id": c["sku_id"],
            "channel": c["channel"],
            "rank": c["rank"],
            "score": c["score"],
            "hook": c["hook"],
            "angle": c["angle"],
            "script": c["script"],
        }
        for c in creatives
    ]
    ids = [f"{c['run_id']}:{c['rank']}" for c in creatives]

    coll.add(documents=documents, metadatas=metadatas, ids=ids)

def query_top_creatives_for_generation(brand_id: str, sku_id: str, channel: str, k: int = 5):
    coll = get_collection("top_creatives")
    brief = f"Best performing ads for brand {brand_id}, sku {sku_id}, channel {channel}"
    results = coll.query(
        query_texts=[brief],
        where={"$and": [{"brand_id": brand_id}, {"sku_id": sku_id}, {"channel": channel}]},
        n_results=k,
    )
    return results

def index_memory_learnings(brand_id, sku_id, key, learnings):
    """distilled learning strings into a separate chroma collection."""
    if not learnings:
        return
    coll = get_collection("memory_learnings")
    # Filter out empty strings
    clean_learnings = [s for s in learnings if s]
    if not clean_learnings:
        return
    documents = clean_learnings
    metadatas = [
        {"brand_id": brand_id, "sku_id": sku_id, "key": key, "index": i}
        for i, _ in enumerate(clean_learnings)
    ]
    ids = [f"{brand_id}:{sku_id}:{key}:{i}" for i, _ in enumerate(clean_learnings)]
    coll.add(documents=documents, metadatas=metadatas, ids=ids)


def query_memory_learnings(brand_id, sku_id, k=5):
    """get up to k relevant learnings for this brand and sku from chroma."""
    coll = get_collection("memory_learnings")
    if coll.count() == 0:
        return []
    brief = f"Key learnings for brand {brand_id}, sku {sku_id}"
    results = coll.query(
        query_texts=[brief],
        where={"$and": [{"brand_id": brand_id}, {"sku_id": sku_id}]},
        n_results=k,
    )
    docs = (results.get("documents") or [[]])[0]
    return [d for d in docs if d]

def compute_novelty_penalty(candidate_text: str, brand_id: str, sku_id: str, channel: str) -> float:
    coll = get_collection("top_creatives")

    # If we’ve never stored any winners yet, there’s nothing to compare against.
    if coll.count() == 0:
        return 0.0

    results = coll.query(
        query_texts=[candidate_text],
        where={"$and": [{"brand_id": brand_id}, {"sku_id": sku_id}, {"channel": channel}]},
        n_results=5,
    )

    distances = results.get("distances") or []
    if not distances or not distances[0]:
        return 0.0

    # smaller distance means more similar, less penalty
    min_distance = min(distances[0])

    if min_distance < 0.2:
        # too close => more penalty
        return -1.0
    if min_distance < 0.4:
        # Somewhat similar => mild penalty
        return -0.5
    return 0.0