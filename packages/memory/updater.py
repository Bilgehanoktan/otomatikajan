import json
from pathlib import Path

def get_memory_data() -> dict:
    """
    Retrieves memory data from the vault.
    """
    # Attempt to load from the actual runtime path if it exists
    # Inside the container, it's mapped via volumes
    vault_path = Path("runtime/data/memory_vault/memory.json")
    if vault_path.exists():
        try:
            return json.loads(vault_path.read_text(encoding="utf-8"))
        except Exception:
            pass
            
    return {
        "version": "1.0",
        "lastUpdated": "",
        "user": {
            "workContext": {"summary": "", "updatedAt": ""},
            "personalContext": {"summary": "", "updatedAt": ""},
            "topOfMind": {"summary": "", "updatedAt": ""}
        },
        "history": {
            "recentMonths": {"summary": "", "updatedAt": ""},
            "earlierContext": {"summary": "", "updatedAt": ""},
            "longTermBackground": {"summary": "", "updatedAt": ""}
        },
        "facts": []
    }

def reload_memory_data() -> dict:
    """Reloads memory data."""
    return get_memory_data()
