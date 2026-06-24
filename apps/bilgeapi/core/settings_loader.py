import yaml
from pathlib import Path
from typing import Any, Dict, Optional

class SettingsLoader:
    """
    Handles reading and parsing configurations from the `.bilgeapi` directory.
    """

    def __init__(self, workspace_dir: Path):
        self.workspace_dir = workspace_dir

    def load_yaml(self, filename: str) -> Dict[str, Any]:
        """
        Safely loads a YAML file from the workspace directory.
        Returns an empty dictionary if the file is missing or invalid.
        """
        filepath = self.workspace_dir / filename
        if not filepath.exists():
            return {}
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = yaml.safe_load(f)
                return content if isinstance(content, dict) else {}
        except Exception:
            return {}

    def get_system_config(self) -> Dict[str, Any]:
        return self.load_yaml("system.yaml")

    def get_permissions(self) -> Dict[str, Any]:
        return self.load_yaml("permissions.yaml")

    def get_risk_rules(self) -> Dict[str, Any]:
        return self.load_yaml("risk_rules.yaml")

    def get_delete_policy(self) -> Dict[str, Any]:
        return self.load_yaml("delete_policy.yaml")

    def get_task_policy(self) -> Dict[str, Any]:
        return self.load_yaml("task_policy.yaml")

    def get_audit_policy(self) -> Dict[str, Any]:
        return self.load_yaml("audit_policy.yaml")
