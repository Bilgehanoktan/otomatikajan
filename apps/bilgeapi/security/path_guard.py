import os
from pathlib import Path

class PathGuard:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()

    def validate_and_resolve(self, filepath: str, allow_internal: bool = False) -> Path:
        """
        Validates the file path at runtime.
        Checks for path traversal, protected files/folders, and directory escape.
        
        Args:
            filepath: The target file path.
            allow_internal: If True, allows accessing the internal '.bilgeapi' directory.
            
        Returns:
            Path: The resolved absolute Path object.
            
        Raises:
            ValueError: If path validation fails.
        """
        # 1. Normalize slashes
        normalized = filepath.replace('\\', '/')
        parts = normalized.split('/')
        
        # 2. Prevent path traversal
        if '..' in parts:
            raise ValueError("Path traversal attempt detected: '..' is not allowed")

        # 3. Resolve absolute path
        try:
            # We use project_root as base for relative paths
            target_path = Path(self.project_root / filepath).resolve()
        except Exception as e:
            raise ValueError(f"Failed to resolve path: {e}")

        # 4. Prevent escaping the project root directory
        try:
            # Check if target_path starts with project_root
            target_path.relative_to(self.project_root)
        except ValueError:
            raise ValueError(f"Path escape detected: path '{filepath}' is outside project root")

        # 5. Check for protected files/folders
        resolved_parts = target_path.parts
        resolved_parts_lower = [p.lower() for p in resolved_parts]
        
        # Prevent accessing .git folder
        if '.git' in resolved_parts_lower:
            raise ValueError("Access to '.git' folder is protected and forbidden")
            
        # Prevent accessing .bilgeapi folder unless explicitly allowed
        if '.bilgeapi' in resolved_parts_lower and not allow_internal:
            raise ValueError("Access to '.bilgeapi' folder is protected and forbidden for external operations")

        # Prevent accessing sensitive files
        filename = resolved_parts[-1].lower() if resolved_parts else ""
        if filename.startswith('.env') or '.env' in filename:
            raise ValueError("Access to environment configuration files is forbidden")
        if filename.endswith('.key') or filename.endswith('.pem'):
            raise ValueError("Access to private key files is forbidden")
        if filename.endswith('.db') or filename.endswith('.sqlite') or filename.endswith('.sqlite3'):
            # Only allow database files if allow_internal is True (e.g. SQLite memory DB)
            if not allow_internal:
                raise ValueError("Access to database files is forbidden")

        return target_path
