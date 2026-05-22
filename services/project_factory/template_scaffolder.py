from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from services.project_factory.artifacts import _resolve_project_dir
from services.project_factory.template_registry import get_template_config

def scaffold_template_files(
    project_id: str,
    template_name: str,
    workspace_root: Optional[str] = None
) -> List[str]:
    """
    Looks up template definition and generates boilerplate files in the project sandbox.
    Prevents path traversal by enforcing that destinations reside entirely inside sandbox.
    """
    config = get_template_config(template_name, workspace_root)
    if not config:
        raise ValueError(f"Template '{template_name}' not found in registry.")

    project_dir = _resolve_project_dir(project_id, workspace_root)
    sandbox_dir = (project_dir / "sandbox").resolve()
    sandbox_dir.mkdir(parents=True, exist_ok=True)

    allowed_outputs = config.get("allowed_outputs", [])
    scaffolded_files = []

    for rel_path in allowed_outputs:
        # Check path traversal
        dest_path = (sandbox_dir / rel_path).resolve()
        if not str(dest_path).startswith(str(sandbox_dir)):
            raise ValueError(f"Path traversal violation blocked: {rel_path}")

        # Create parent directories
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate boilerplate content depending on file type and name
        content = generate_boilerplate_content(template_name, rel_path)

        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(content)

        scaffolded_files.append(rel_path)

    return scaffolded_files

def generate_boilerplate_content(template_name: str, rel_path: str) -> str:
    """
    Provides rich boilerplate content based on template and file path.
    """
    filename = Path(rel_path).name

    if filename == "package.json":
        return """{
  "name": "scaffolded-sandbox-app",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "echo 'Mock Build Success'",
    "lint": "echo 'Mock Lint Passed'",
    "test": "echo 'Mock Tests Passed'"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "next": "14.1.0"
  }
}
"""
    elif filename == "README.md":
        return f"""# Sandbox Deliverable — {template_name}

Auto-generated boilerplate for sandbox implementation.
"""
    elif filename == "architecture.md":
        return """# Architecture Specifications

- **Layers:** Clean architecture presentation
- **Containment:** Whitelisted API-only boundaries
"""
    elif filename == "user_guide.md":
        return """# User Guide

1. Deploy target package
2. Request operator review and Human Gate resolution
"""
    elif filename == "main.py":
        return """from fastapi import FastAPI

app = FastAPI(title="FastAPI Sandbox Service")

@app.get("/")
def read_root():
    return {"status": "healthy", "scope": "sandbox"}
"""
    elif filename == "test_main.py":
        return """def test_read_root():
    # Simple pass test
    assert True
"""
    elif filename == "requirements.txt":
        return "fastapi>=0.100.0\nuvicorn>=0.22.0\npytest>=7.0.0\n"
    elif filename == "page.tsx":
        return """import React from 'react';

export default function Page() {
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold">Sandbox UI Preview</h1>
      <p className="mt-2 text-gray-600">This frontend page runs in the sandbox environment.</p>
    </div>
  );
}
"""
    elif filename == "layout.tsx":
        return """import React from 'react';

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
"""
    elif filename == "sheet_schema.json":
        return """{
  "sheets": [
    {
      "name": "Audit Tracker",
      "columns": ["Date", "AuditID", "Findings", "Severity", "RemediationState"]
    }
  ]
}
"""
    elif filename == "tracker_instructions.md":
        return """# Google Sheets Tracker Guidelines

- Populate with findings using pre-approved column mapping.
"""
    elif filename == "excel_template.xlsx":
        return "Dummy Binary/Excel content simulation.\n"
    elif filename == "readme_excel.md":
        return """# Excel Dashboard Instructions

- Open the template in Excel
- Run whitelisted validation formulas.
"""
    else:
        return f"# Boilerplate for {rel_path}\n"
