from __future__ import annotations

import os
import shutil
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from services.project_factory.models import ProjectFactoryIntake
from services.project_factory.artifacts import _resolve_project_dir, write_sandbox_manifest

# Forbidden extensions and substrings for secret/credential safety
FORBIDDEN_PATTERNS = [
    ".env", "secret", "credential", "token", "password", "key", "pem", "db", "sqlite"
]

FORBIDDEN_SUFFIXES = [
    ".pem", ".key", ".db", ".db.bak", ".sqlite", ".pyc", ".db-journal", ".db-wal"
]

BINARY_EXTENSIONS = [
    ".png", ".jpg", ".jpeg", ".gif", ".zip", ".tar", ".gz", ".exe", ".dll", ".so", ".pdf", ".ico"
]

def is_sensitive_path(path_str: str) -> bool:
    """
    Checks if a file path matches secret or sensitive patterns.
    """
    normalized = path_str.lower()
    # Suffix checks
    if any(normalized.endswith(suffix) for suffix in FORBIDDEN_SUFFIXES):
        return True
    # Substring checks in the final filename
    filename = os.path.basename(normalized)
    if any(pattern in filename for pattern in FORBIDDEN_PATTERNS):
        return True
    return False

def is_binary_file(path: Path) -> bool:
    """
    Checks if a file has a binary extension or cannot be decoded as text.
    """
    if path.suffix.lower() in BINARY_EXTENSIONS:
        return True
    # Try decoding a chunk of the file
    try:
        with open(path, "rb") as f:
            chunk = f.read(1024)
            if b"\x00" in chunk:
                return True
            # Attempt to decode as UTF-8
            chunk.decode("utf-8")
    except Exception:
        return True
    return False

def scaffold_project_sandbox(
    project_brief: ProjectFactoryIntake,
    workspace_root: Optional[str] = None
) -> Dict[str, Any]:
    """
    Scaffolds a secure sandbox project directory under project_outputs/project_factory/{project_id}/sandbox/.
    Copies affected files subject to strict security containment checks.
    """
    if not workspace_root:
        workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    workspace_path = Path(workspace_root).resolve()
    project_dir = _resolve_project_dir(project_brief.project_id, workspace_root)
    sandbox_dir = (project_dir / "sandbox").resolve()

    # Destination Traversal Check
    if not str(sandbox_dir).startswith(str(project_dir)):
        raise ValueError("Sandbox path traversal violation: target directory outside project outputs")

    sandbox_dir.mkdir(parents=True, exist_ok=True)

    copied_files: List[str] = []
    skipped_files: List[Dict[str, str]] = []
    placeholder_files: List[str] = []

    for rel_path in project_brief.affected_files:
        if not rel_path:
            continue
            
        # 1. Source Traversal Check
        src_path = (workspace_path / rel_path).resolve()
        if not str(src_path).startswith(str(workspace_path)):
            skipped_files.append({
                "path": rel_path,
                "reason": "Path traversal check failed (source is outside workspace)."
            })
            continue

        # 2. Destination Traversal Check for copy
        dest_path = (sandbox_dir / rel_path).resolve()
        if not str(dest_path).startswith(str(sandbox_dir)):
            skipped_files.append({
                "path": rel_path,
                "reason": "Path traversal check failed (destination is outside sandbox)."
            })
            continue

        # 3. Secret/Env check
        if is_sensitive_path(rel_path):
            skipped_files.append({
                "path": rel_path,
                "reason": "Sensitive file match blocked (secret/credentials protection)."
            })
            continue

        # 4. Check if file exists in primary repo
        if src_path.exists() and src_path.is_file():
            # Size limit check (1MB)
            size = src_path.stat().st_size
            if size > 1_000_000:
                skipped_files.append({
                    "path": rel_path,
                    "reason": f"File size too large ({size} bytes, limit is 1MB)."
                })
                continue
                
            # Binary check
            if is_binary_file(src_path):
                skipped_files.append({
                    "path": rel_path,
                    "reason": "Binary files are skipped for safety."
                })
                continue

            # Perform safe copy
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dest_path)
            copied_files.append(rel_path)
        else:
            # File does not exist in repo; initialize a safe placeholder file
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            with open(dest_path, "w", encoding="utf-8") as f:
                f.write(f"# Placeholder for {rel_path}\n# Created automatically by Project Factory Scaffolder.\n")
            placeholder_files.append(rel_path)

    # 5. Generate README.md in sandbox
    readme_path = sandbox_dir / "README.md"
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(f"# Sandbox Workspace: {project_brief.project_id}\n\n")
        f.write(f"**Title:** {project_brief.title}\n")
        f.write(f"**Intake ID:** {project_brief.project_id}\n")
        f.write(f"**State:** SCOPE_APPROVED\n")
        f.write(f"**Scaffolded At:** {datetime.now(timezone.utc).isoformat()}Z\n\n")
        f.write("## Problem Statement\n")
        f.write(f"{project_brief.problem_statement}\n\n")
        f.write("## Recommended Action\n")
        f.write(f"{project_brief.recommended_action}\n\n")
        f.write("## Sandbox Files\n")
        if copied_files:
            f.write("### Copied Files:\n")
            for cf in copied_files:
                f.write(f"- `{cf}`\n")
        if placeholder_files:
            f.write("### Initialized Placeholders:\n")
            for pf in placeholder_files:
                f.write(f"- `{pf}`\n")

    # 6. Generate and save the manifest
    manifest = {
        "project_id": project_brief.project_id,
        "created_at": datetime.now(timezone.utc).isoformat() + "Z",
        "status": "SCAFFOLD_COMPLETED",
        "sandbox_path": f"project_outputs/project_factory/{project_brief.project_id}/sandbox",
        "copied_files": copied_files,
        "skipped_files": skipped_files,
        "placeholder_files": placeholder_files
    }
    
    write_sandbox_manifest(project_brief.project_id, manifest, workspace_root)

    return manifest
