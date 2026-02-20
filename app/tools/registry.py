"""
Tool registry with schema validation.
"""

from app.tools.brand_guidelines import get_brand_guidelines
from app.tools.past_creatives import search_past_creatives
from app.tools.artifact_logger import log_artifact
from app.tools.memory_tools import retrieve_memory, write_memory

# Schema: tool_name -> {"params": [{"name": str, "type": type, "required": bool}], "fn": callable}
TOOLS = {
    "get_brand_guidelines": {
        "params": [{"name": "brand_id", "type": str, "required": True}],
        "fn": get_brand_guidelines,
    },
    "search_past_creatives": {
        "params": [
            {"name": "brand_id", "type": str, "required": True},
            {"name": "sku_id", "type": str, "required": True},
            {"name": "channel", "type": str, "required": True},
            {"name": "query", "type": str, "required": False},
            {"name": "k", "type": int, "required": True},
        ],
        "fn": search_past_creatives,
    },
    "log_artifact": {
        "params": [
            {"name": "run_id", "type": str, "required": True},
            {"name": "artifact_type", "type": str, "required": True},
            {"name": "payload", "type": dict, "required": True},
        ],
        "fn": log_artifact,
    },
    "retrieve_memory": {
        "params": [
            {"name": "brand_id", "type": str, "required": True},
            {"name": "sku_id", "type": str, "required": True},
            {"name": "key", "type": str, "required": True},
        ],
        "fn": retrieve_memory,
    },
    "write_memory": {
        "params": [
            {"name": "brand_id", "type": str, "required": True},
            {"name": "sku_id", "type": str, "required": True},
            {"name": "key", "type": str, "required": True},
            {"name": "value", "type": str, "required": True},
        ],
        "fn": write_memory,
    },
}


def validate_args(tool_name, kwargs):
    """Raise ValueError if kwargs do not match the tool schema."""
    if tool_name not in TOOLS:
        raise ValueError(f"Unknown tool: {tool_name}")
    spec = TOOLS[tool_name]
    for p in spec["params"]:
        name = p["name"]
        if p["required"] and name not in kwargs:
            raise ValueError(f"Missing required argument: {name}")
        if name in kwargs:
            expected = p["type"]
            val = kwargs[name]
            if expected is int and not isinstance(val, int):
                try:
                    kwargs[name] = int(val)
                except (TypeError, ValueError):
                    raise ValueError(f"{name} must be int, got {type(val).__name__}")
            elif expected is str and not isinstance(val, str):
                kwargs[name] = str(val) if val is not None else ""
            elif expected is dict and not isinstance(val, dict):
                raise ValueError(f"{name} must be dict, got {type(val).__name__}")
    return kwargs


def run_tool(tool_name, **kwargs):
    """Validate and execute a tool by name. Returns the tool result."""
    kwargs = validate_args(tool_name, kwargs)
    fn = TOOLS[tool_name]["fn"]
    return fn(**kwargs)


def list_tools():
    """Return tool names and their parameter schemas for discovery."""
    return {
        name: {
            "params": [p["name"] for p in spec["params"]],
            "required": [p["name"] for p in spec["params"] if p["required"]],
        }
        for name, spec in TOOLS.items()
    }
