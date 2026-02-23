import json
import os

GUIDELINES_PATH = os.path.join("data", "brand_guidelines.json")

def get_brand_guidelines(brand_id):
    """Load guidelines from data/brand_guidelines.json. Returns {} for unknown brands."""
    if not GUIDELINES_PATH.exists():
        return {}
    try:
        with open(GUIDELINES_PATH, "r") as f:
            data = json.load(f)
        return data.get(brand_id, {})
    except (json.JSONDecodeError, OSError):
        return {}
