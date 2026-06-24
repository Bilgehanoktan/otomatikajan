from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
import yaml
from apps.bilgeapi.core.discovery import SystemDiscovery
from apps.bilgeapi.core.settings_loader import SettingsLoader

class SystemProfiler:
    """
    Compiles discovery results and yaml configurations to build a system profile.
    Saves the profile to system.yaml.
    """

    def __init__(self, project_root: Path, workspace_dir: Path):
        self.project_root = project_root
        self.workspace_dir = workspace_dir
        self.discovery = SystemDiscovery(project_root)
        self.loader = SettingsLoader(workspace_dir)

    def build_profile(self) -> Dict[str, Any]:
        """
        Gathers system information and builds a system profile dictionary.
        """
        system_yaml = self.loader.get_system_config()
        
        # Determine system name (fallback to directory name)
        system_name = system_yaml.get("system_name") or self.project_root.name
        
        # Auto-discover project characteristics
        project_type = self.discovery.discover_project_type()
        commands = self.discovery.discover_commands(project_type)
        file_tree = self.discovery.scan_file_tree()

        profile = {
            "system_name": system_name,
            "project_type": project_type,
            "environment": system_yaml.get("environment") or "development",
            "start_command": system_yaml.get("start_command") or commands["start"],
            "test_command": system_yaml.get("test_command") or commands["test"],
            "file_count": len(file_tree),
            "file_tree": file_tree,
            "last_scanned_at": datetime.now(timezone.utc).isoformat(),
        }

        # Keep created_at value stable
        if "created_at" in system_yaml and system_yaml["created_at"]:
            profile["created_at"] = system_yaml["created_at"]
        else:
            profile["created_at"] = datetime.now(timezone.utc).isoformat()

        # Update system.yaml with discovered fields
        self.save_profile(profile)

        return profile

    def save_profile(self, profile: Dict[str, Any]) -> None:
        """
        Saves profile data back into system.yaml while omitting large fields like file_tree.
        """
        yaml_data = {
            "system_name": profile["system_name"],
            "project_type": profile["project_type"],
            "environment": profile["environment"],
            "start_command": profile["start_command"],
            "test_command": profile["test_command"],
            "created_at": profile["created_at"],
            "last_scanned_at": profile["last_scanned_at"],
        }
        
        filepath = self.workspace_dir / "system.yaml"
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                yaml.safe_dump(yaml_data, f, default_flow_style=False, sort_keys=False)
        except Exception:
            pass
