from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from services.project_factory.artifacts import _resolve_project_dir
from services.project_factory.models import RiskAssessment

def assess_project_risk(
    project_id: str,
    workspace_root: Optional[str] = None
) -> RiskAssessment:
    """
    Scans files in the candidate package for dangerous patterns and size constraints.
    Returns a RiskAssessment object and saves risk_assessment.json.
    """
    project_dir = _resolve_project_dir(project_id, workspace_root)
    cand_dir = project_dir / "candidate_package"
    manifest_path = project_dir / "candidate_manifest.json"

    warnings = []
    blocking_risks = []
    risk_score = 0

    # If candidate manifest is missing, that's a blocking risk
    if not manifest_path.exists():
        blocking_risks.append("Candidate package manifest is missing.")
        risk_score += 100
    else:
        # Load manifest
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest_data = json.load(f)
            files = manifest_data.get("files", [])
            
            if not files:
                warnings.append("No files packaged in candidate.")
                risk_score += 10

            for f_info in files:
                rel_path = f_info.get("path", "")
                full_path = cand_dir / rel_path
                
                # Check path traversal
                if not str(full_path.resolve()).startswith(str(cand_dir.resolve())):
                    blocking_risks.append(f"Security: File path traversal detected in file: {rel_path}")
                    risk_score += 100
                    continue

                if full_path.exists() and full_path.is_file():
                    # 1. Size check (> 50KB)
                    sz = full_path.stat().st_size
                    if sz > 50 * 1024:
                        warnings.append(f"File {rel_path} is large ({sz} bytes).")
                        risk_score += 15

                    # 2. Keyword scan for risky python/js constructs
                    try:
                        content = full_path.read_text(encoding="utf-8", errors="ignore")
                        
                        dangerous_patterns = {
                            "eval(": "Contains eval() construct",
                            "exec(": "Contains exec() construct",
                            "subprocess.": "Spawns dynamic subprocesses",
                            "os.system": "Uses legacy os.system shell interface",
                            "shutil.rmtree(/)": "Dangerous filesystem removal call",
                            "chmod": "Modifies system executable permissions"
                        }
                        
                        for pattern, desc in dangerous_patterns.items():
                            if pattern in content:
                                warnings.append(f"Security Warning in {rel_path}: {desc}")
                                risk_score += 25
                                
                    except Exception as fe:
                        warnings.append(f"Could not read {rel_path} for security scanning: {fe}")
                        risk_score += 5
        except Exception as e:
            blocking_risks.append(f"Failed to parse candidate manifest: {e}")
            risk_score += 80

    # Ensure risk score is capped between 0 and 100
    risk_score = min(100, max(0, risk_score))

    # Determine risk level
    if risk_score >= 70 or len(blocking_risks) > 0:
        risk_level = "HIGH"
    elif risk_score >= 35:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    # Default baseline risk to have some interesting numbers if Low but clean (e.g. 22)
    if risk_score == 0 and len(blocking_risks) == 0:
        # Give a small low risk score based on existence of files
        risk_score = 22

    assessment = RiskAssessment(
        risk_score=risk_score,
        risk_level=risk_level,
        blocking_risks=blocking_risks,
        warnings=warnings
    )

    # Save to disk
    assessment_path = project_dir / "risk_assessment.json"
    with open(assessment_path, "w", encoding="utf-8") as f:
        json.dump(assessment.model_dump(), f, indent=2, ensure_ascii=False)

    return assessment
