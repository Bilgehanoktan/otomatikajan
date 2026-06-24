import os
from pathlib import Path
from typing import Any, Dict, List

class SystemDiscovery:
    """
    Scans the workspace to profile the project type, structure, and commands.
    """

    EXCLUDE_DIRS = {
        "node_modules", ".git", ".venv", "venv", "__pycache__", 
        ".pytest_cache", ".mypy_cache", ".ruff_cache", ".bilgeapi", 
        ".next", "dist", "build", "artifacts", "scratch", "runtime"
    }

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def discover_project_type(self) -> str:
        """
        Detects the primary project type based on file structure.
        """
        if (self.project_root / "package.json").exists():
            return "NodeJS/TypeScript"
        if (self.project_root / "pyproject.toml").exists() or (self.project_root / "requirements.txt").exists():
            return "Python"
        if (self.project_root / "go.mod").exists():
            return "Go"
        if (self.project_root / "Cargo.toml").exists():
            return "Rust"
        return "Unknown"

    def discover_commands(self, project_type: str) -> Dict[str, str]:
        """
        Identifies default start and test commands based on the project type.
        """
        commands = {"start": "", "test": ""}
        if project_type == "NodeJS/TypeScript":
            commands["start"] = "npm run dev"
            commands["test"] = "npm test"
        elif project_type == "Python":
            # Check for pytest or fallback to unittest
            commands["test"] = "pytest" if self._has_pytest_installed() else "python -m unittest"
            # Detect starting script
            if (self.project_root / "apps" / "bilgeapi" / "main.py").exists():
                commands["start"] = "uvicorn apps.bilgeapi.main:app --reload"
            elif (self.project_root / "main.py").exists():
                commands["start"] = "python main.py"
        elif project_type == "Go":
            commands["start"] = "go run main.go"
            commands["test"] = "go test ./..."
        elif project_type == "Rust":
            commands["start"] = "cargo run"
            commands["test"] = "cargo test"
        return commands

    def _has_pytest_installed(self) -> bool:
        try:
            import pytest
            return True
        except ImportError:
            return False

    def scan_file_tree(self, max_depth: int = 4) -> List[str]:
        """
        Generates a simplified relative file path list up to a maximum depth.
        Filters out directories listed in EXCLUDE_DIRS.
        """
        file_list: List[str] = []
        self._walk_tree(self.project_root, "", 0, max_depth, file_list)
        return file_list

    def _walk_tree(self, current_dir: Path, rel_path: str, depth: int, max_depth: int, file_list: List[str]):
        if depth > max_depth:
            return
        
        try:
            for entry in current_dir.iterdir():
                if entry.name in self.EXCLUDE_DIRS:
                    continue
                
                entry_rel = f"{rel_path}/{entry.name}" if rel_path else entry.name
                if entry.is_file():
                    file_list.append(entry_rel)
                elif entry.is_dir():
                    file_list.append(entry_rel + "/")
                    self._walk_tree(entry, entry_rel, depth + 1, max_depth, file_list)
        except PermissionError:
            pass
