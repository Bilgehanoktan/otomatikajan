from __future__ import annotations

import os
from pathlib import Path
import yaml
from typing import Dict, Any, Optional

def load_template_registry(workspace_root: Optional[str] = None) -> Dict[str, Any]:
    """
    Loads templates/project_factory/template_registry.yaml and returns the parsed config.
    """
    if not workspace_root:
        workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    registry_path = Path(workspace_root) / "templates" / "project_factory" / "template_registry.yaml"
    if not registry_path.exists():
        # Fallback dictionary if YAML is missing
        return {
            "templates": {
                "documentation-pack": {
                    "type": "docs",
                    "allowed_outputs": ["README.md", "architecture.md", "user_guide.md"],
                    "test_commands": []
                },
                "fastapi-service": {
                    "type": "backend",
                    "allowed_outputs": ["main.py", "requirements.txt", "test_main.py"],
                    "test_commands": ["py -3.13 -m pytest"]
                }
            }
        }

    with open(registry_path, "r", encoding="utf-8") as f:
        try:
            return yaml.safe_load(f) or {}
        except Exception:
            return {}

def get_template_config(template_name: str, workspace_root: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Retrieves the configuration for a specific template name, returning None if not found.
    """
    registry = load_template_registry(workspace_root)
    templates = registry.get("templates", {})
    return templates.get(template_name)
