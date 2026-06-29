from typing import Any, Dict, List
from pathlib import Path
from apps.bilgeapi.core.settings_loader import SettingsLoader

class HealthScorer:
    """
    Evaluates workspace health based on configurations, missing files, 
    and general project readiness parameters.
    """

    def __init__(self, project_root: Path, workspace_dir: Path):
        self.project_root = project_root
        self.workspace_dir = workspace_dir
        self.loader = SettingsLoader(workspace_dir)

    def calculate_score(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates a system health score from 0.0 to 100.0.
        Returns a dictionary containing the score, grade, and findings list.
        """
        score = 100.0
        findings: List[str] = []

        # 1. Project Type Check
        if profile.get("project_type") == "Unknown":
            score -= 20.0
            findings.append("UNKNOWN_PROJECT_TYPE: System could not auto-detect the project framework.")

        # 2. Critical Commands Check
        if not profile.get("test_command"):
            score -= 15.0
            findings.append("MISSING_TEST_COMMAND: No test command detected or configured.")
        if not profile.get("start_command"):
            score -= 10.0
            findings.append("MISSING_START_COMMAND: No start command detected or configured.")

        # 3. Critical Files Check
        critical_files = [
            (".gitignore", "Missing .gitignore file in project root."),
            ("README.md", "Missing README.md documentation file."),
        ]
        for filename, warning in critical_files:
            if not (self.project_root / filename).exists():
                score -= 10.0
                findings.append(f"MISSING_CRITICAL_FILE: {warning}")

        # 4. Permissions Config Check
        permissions = self.loader.get_permissions().get("permissions", {})
        if not permissions.get("deny"):
            score -= 10.0
            findings.append("INSECURE_PERMISSIONS: The permissions.yaml deny list is empty or missing.")

        # 5. Secrets Exposure Check (Search for raw key/cert files in the codebase)
        import os
        exclude_dirs = {
            "node_modules", ".git", ".venv", "venv", "__pycache__", 
            ".pytest_cache", ".mypy_cache", ".ruff_cache", ".bilgeapi", 
            ".next", "dist", "build", "artifacts", "scratch", "runtime",
            ".nx", ".agents", ".gemini", ".agent", ".backup", ".codex", 
            ".codex_skill_staging", ".deer-flow", ".legacy_archive", 
            ".playwright-browsers", ".pydeps314", "brain", "tmp", 
            "tmp_test_outputs", "uploads", "project_outputs", "repair_outputs", "reports"
        }
        key_files = []
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for file in files:
                if file.endswith(".pem") or file.endswith(".key"):
                    key_files.append(Path(root) / file)

        for kf in key_files:
            rel_str = str(kf.relative_to(self.project_root))
            score -= 15.0
            findings.append(f"EXPOSED_SECRET_FILE: Private key/cert found exposed in project: {rel_str}")

        # Ensure score bounds
        score = max(0.0, score)

        # Grade calculation
        if score >= 90.0:
            grade = "A"
        elif score >= 80.0:
            grade = "B"
        elif score >= 70.0:
            grade = "C"
        elif score >= 60.0:
            grade = "D"
        else:
            grade = "F"

        return {
            "score": score,
            "grade": grade,
            "findings": findings,
            "status": "HEALTHY" if score >= 80.0 else "DEGRADED" if score >= 50.0 else "UNHEALTHY"
        }
