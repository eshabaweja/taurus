from app.storage.db import get_memory_entries, create_memory_entry


def retrieve_memory(brand_id, sku_id, key):
    """Pulls previous winning insights from storage."""
    entries = get_memory_entries(brand_id, sku_id, key=key)
    return [{"key": e["key"], "value": e["value"]} for e in entries]


def write_memory(brand_id, sku_id, key, value):
    """Stores distilled learnings from previous runs."""
    create_memory_entry(brand_id, sku_id, key, value)
    return {"ok": True, "brand_id": brand_id, "sku_id": sku_id, "key": key}
