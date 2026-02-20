import json
from pathlib import Path

DATA_PATH = Path("data/creatives.json")


def search_past_creatives(brand_id, sku_id, channel, query, k):
    """Returns top-k past creatives from local dataset. """
    with open(DATA_PATH, "r") as f:
        creatives = json.load(f)

    filtered = [
        c
        for c in creatives
        if c.get("brand_id") == brand_id and c.get("sku_id") == sku_id and c.get("channel") == channel
    ]

    if query and query.strip():
        q = query.strip().lower()
        filtered = [
            c
            for c in filtered
            if q in (c.get("hook") or "").lower()
            or q in (c.get("angle") or "").lower()
            or q in (c.get("script") or "").lower()
        ]

    # Sort by CTR descending (best performers first), then take top k
    filtered.sort(key=lambda c: (c.get("ctr") or 0), reverse=True)
    top_k = filtered[: max(0, int(k))]

    return [
        {
            "hook": c.get("hook"),
            "angle": c.get("angle"),
            "script": c.get("script"),
            "metrics": {"ctr": c.get("ctr"), "cvr": c.get("cvr"), "cpa": c.get("cpa")},
            "notes": c.get("notes", ""),
        }
        for c in top_k
    ]
