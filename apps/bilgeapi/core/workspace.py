import os
import yaml
from pathlib import Path
from typing import Optional

DEFAULT_SYSTEM_YAML = """# BilgeAPI System Configuration
system_name: "Auto-Discovered Project"
project_type: "unknown"
environment: "development"
created_at: null
last_scanned_at: null
llm_model: "llama3.1:8b"
llm_fallback_model: "mistral:7b"
llm_low_resource_model: "gemma3:4b"
llm_timeout_s: 60.0
"""

DEFAULT_PERMISSIONS_YAML = """# BilgeAPI Action Permissions
permissions:
  allow:
    - "Read"
    - "Grep"
    - "Glob"
  ask:
    - "Bash"
    - "Write"
    - "Edit"
    - "MultiEdit"
  deny:
    - "sudo *"
    - "rm -rf *"
    - "chmod 777 *"
    - "ssh *"
    - "* > /dev/*"
"""

DEFAULT_RISK_RULES_YAML = """# BilgeAPI Path Risk Rules
rules:
  - path_pattern: "**/auth/*"
    risk_level: "HIGH"
    reason: "Authentication files require manual verification"
  - path_pattern: "**/.env*"
    risk_level: "CRITICAL"
    reason: "Environment configuration files are highly sensitive"
  - path_pattern: "**/*.db*"
    risk_level: "CRITICAL"
    reason: "Database files must not be altered automatically"
  - path_pattern: "**/migrations/*"
    risk_level: "HIGH"
    reason: "Database migrations require structural safety validation"
  - path_pattern: "**/*.key"
    risk_level: "CRITICAL"
    reason: "Private keys are forbidden from automatic operations"
  - path_pattern: "**/*.pem"
    risk_level: "CRITICAL"
    reason: "Private keys are forbidden from automatic operations"
"""

DEFAULT_DELETE_POLICY_YAML = """# BilgeAPI File Deletion & Quarantine Policy
policy:
  auto_delete:
    - "**/__pycache__/*"
    - "**/.pytest_cache/*"
    - "**/.mypy_cache/*"
    - "**/.ruff_cache/*"
    - "**/node_modules/.cache/*"
    - "**/dist/*"
    - "**/build/*"
    - "**/coverage/*"
    - "**/*.tmp"
    - "**/.DS_Store"
  quarantine:
    - "**/*.bak"
    - "**/backup_*"
    - "**/duplicate_*"
  approval_required:
    - "**/.env*"
    - "**/config.yaml"
    - "**/settings.py"
    - "**/package.json"
    - "**/pyproject.toml"
    - "**/requirements.txt"
    - "**/Dockerfile"
    - "**/docker-compose.yml"
    - "**/src/**/*"
    - "**/app/**/*"
    - "**/tests/**/*"
    - "**/test_*.py"
  forbidden:
    - "**/.git/**/*"
    - "**/.bilgeapi/**/*"
    - "**/audit.log"
    - "**/*.key"
    - "**/*.pem"
"""

DEFAULT_TASK_POLICY_YAML = """# BilgeAPI Task Execution Policy
policy:
  max_concurrency: 4
  retry_limit: 3
  timeout_seconds: 600
  low_risk_auto_execute: true
"""

DEFAULT_AUDIT_POLICY_YAML = """# BilgeAPI Audit and Decision Logging Policy
policy:
  log_level: "INFO"
  retention_days: 90
  include_args: true
  hash_before_after: true
"""


class WorkspaceManager:
    """
    Manages the lifecycle of the portable `.bilgeapi` workspace.
    Locates the project root and initializes necessary configurations and directories.
    """

    def __init__(self, start_path: Optional[str] = None):
        self.start_path = Path(start_path or os.getcwd()).resolve()
        self.project_root = self.find_project_root(self.start_path)
        self.workspace_dir = self.project_root / ".bilgeapi"

    def find_project_root(self, current_path: Path) -> Path:
        """
        Recursively searches upward for project markers to identify the root directory.
        """
        markers = ["package.json", "pyproject.toml", ".git", "requirements.txt", "alembic.ini"]
        
        # Traverse upward to find any marker file/directory
        for parent in [current_path] + list(current_path.parents):
            for marker in markers:
                if (parent / marker).exists():
                    return parent
        
        # Fallback to current working directory
        return current_path

    def initialize_workspace(self) -> dict[str, str]:
        """
        Creates the `.bilgeapi` directory and its subfolders, and generates default yaml configs if missing.
        Returns a dictionary mapping of initialized files/folders.
        """
        subdirs = ["logs", "reports", "quarantine", "memory", "audit"]
        created = {}

        # 1. Create main workspace folder
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        created[".bilgeapi"] = str(self.workspace_dir)

        # 2. Create subfolders
        for subdir in subdirs:
            p = self.workspace_dir / subdir
            p.mkdir(parents=True, exist_ok=True)
            created[f".bilgeapi/{subdir}"] = str(p)

        # 3. Create default configuration files if missing
        configs = {
            "system.yaml": DEFAULT_SYSTEM_YAML,
            "permissions.yaml": DEFAULT_PERMISSIONS_YAML,
            "risk_rules.yaml": DEFAULT_RISK_RULES_YAML,
            "delete_policy.yaml": DEFAULT_DELETE_POLICY_YAML,
            "task_policy.yaml": DEFAULT_TASK_POLICY_YAML,
            "audit_policy.yaml": DEFAULT_AUDIT_POLICY_YAML,
        }

        for filename, content in configs.items():
            filepath = self.workspace_dir / filename
            if not filepath.exists():
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content.strip() + "\n")
                created[f".bilgeapi/{filename}"] = "CREATED"
            else:
                created[f".bilgeapi/{filename}"] = "EXISTS"

        return created
