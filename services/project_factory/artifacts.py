from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from services.project_factory.models import ProjectFactoryIntake, RequirementGate

def _resolve_project_dir(project_id: str, workspace_root: Optional[str] = None) -> Path:
    if not workspace_root:
        workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    workspace_path = Path(workspace_root).resolve()
    project_factory_base = (workspace_path / "project_outputs" / "project_factory").resolve()
    project_dir = (project_factory_base / project_id).resolve()

    # Path traversal protection
    if not str(project_dir).startswith(str(project_factory_base)):
        raise ValueError("Path traversal violation detected: attempted access outside project_outputs/project_factory/")

    return project_dir

def write_project_factory_artifacts(
    intake: ProjectFactoryIntake,
    gate: RequirementGate,
    workspace_root: Optional[str] = None
) -> None:
    """
    Safely writes project_brief.json and requirement_gate.json to the project_outputs/project_factory/{project_id} directory.
    Enforces strict path traversal prevention checks.
    """
    project_dir = _resolve_project_dir(intake.project_id, workspace_root)
    project_dir.mkdir(parents=True, exist_ok=True)

    # 1. Write project_brief.json
    brief_path = project_dir / "project_brief.json"
    with open(brief_path, "w", encoding="utf-8") as f:
        json.dump(intake.model_dump(), f, indent=2, ensure_ascii=False)

    # 2. Write requirement_gate.json
    gate_path = project_dir / "requirement_gate.json"
    with open(gate_path, "w", encoding="utf-8") as f:
        json.dump(gate.model_dump(), f, indent=2, ensure_ascii=False)

def load_project_factory_artifacts(
    project_id: str,
    workspace_root: Optional[str] = None
) -> tuple[ProjectFactoryIntake, RequirementGate]:
    """
    Safely loads project_brief.json and requirement_gate.json from the project_outputs/project_factory/{project_id} directory.
    Enforces strict path traversal checks.
    """
    project_dir = _resolve_project_dir(project_id, workspace_root)
    
    brief_path = project_dir / "project_brief.json"
    gate_path = project_dir / "requirement_gate.json"

    if not brief_path.exists() or not gate_path.exists():
        raise FileNotFoundError(f"Project Factory artifacts not found for project: {project_id}")

    with open(brief_path, "r", encoding="utf-8") as f:
        brief_data = json.load(f)
    with open(gate_path, "r", encoding="utf-8") as f:
        gate_data = json.load(f)

    return ProjectFactoryIntake(**brief_data), RequirementGate(**gate_data)

def write_sandbox_manifest(
    project_id: str,
    manifest: Dict[str, Any],
    workspace_root: Optional[str] = None
) -> None:
    """
    Writes the sandbox_manifest.json to the project folder.
    """
    project_dir = _resolve_project_dir(project_id, workspace_root)
    project_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = project_dir / "sandbox_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

def load_apply_preview(
    project_id: str,
    workspace_root: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    project_dir = _resolve_project_dir(project_id, workspace_root)
    preview_path = project_dir / "apply_preview.json"
    if not preview_path.exists():
        return None
    with open(preview_path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_draft_pr_plan(
    project_id: str,
    workspace_root: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    project_dir = _resolve_project_dir(project_id, workspace_root)
    plan_path = project_dir / "draft_pr_plan.json"
    if not plan_path.exists():
        return None
    with open(plan_path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_draft_pr_creation(
    project_id: str,
    creation_data: Dict[str, Any],
    workspace_root: Optional[str] = None
) -> None:
    project_dir = _resolve_project_dir(project_id, workspace_root)
    project_dir.mkdir(parents=True, exist_ok=True)
    creation_path = project_dir / "draft_pr_creation.json"
    with open(creation_path, "w", encoding="utf-8") as f:
        json.dump(creation_data, f, indent=2, ensure_ascii=False)

def load_draft_pr_creation(
    project_id: str,
    workspace_root: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    project_dir = _resolve_project_dir(project_id, workspace_root)
    creation_path = project_dir / "draft_pr_creation.json"
    if not creation_path.exists():
        return None
    with open(creation_path, "r", encoding="utf-8") as f:
        return json.load(f)

# --- Phase 11: PR Review Gate Artifacts ---

def _write_json_artifact(project_id: str, filename: str, data: Dict[str, Any], workspace_root: Optional[str] = None) -> None:
    project_dir = _resolve_project_dir(project_id, workspace_root)
    project_dir.mkdir(parents=True, exist_ok=True)
    with open(project_dir / filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def _load_json_artifact(project_id: str, filename: str, workspace_root: Optional[str] = None) -> Optional[Dict[str, Any]]:
    project_dir = _resolve_project_dir(project_id, workspace_root)
    path = project_dir / filename
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_pr_review_report(project_id: str, data: Dict[str, Any], workspace_root: Optional[str] = None) -> None:
    _write_json_artifact(project_id, "pr_review_report.json", data, workspace_root)

def load_pr_review_report(project_id: str, workspace_root: Optional[str] = None) -> Optional[Dict[str, Any]]:
    return _load_json_artifact(project_id, "pr_review_report.json", workspace_root)

def write_pr_agent_review(project_id: str, data: Dict[str, Any], workspace_root: Optional[str] = None) -> None:
    _write_json_artifact(project_id, "pr_agent_review.json", data, workspace_root)

def load_pr_agent_review(project_id: str, workspace_root: Optional[str] = None) -> Optional[Dict[str, Any]]:
    return _load_json_artifact(project_id, "pr_agent_review.json", workspace_root)

def write_verifier_mesh_report(project_id: str, data: Dict[str, Any], workspace_root: Optional[str] = None) -> None:
    _write_json_artifact(project_id, "verifier_mesh_report.json", data, workspace_root)

def load_verifier_mesh_report(project_id: str, workspace_root: Optional[str] = None) -> Optional[Dict[str, Any]]:
    return _load_json_artifact(project_id, "verifier_mesh_report.json", workspace_root)

def write_pr_review_scorecard(project_id: str, data: Dict[str, Any], workspace_root: Optional[str] = None) -> None:
    _write_json_artifact(project_id, "pr_review_scorecard.json", data, workspace_root)

def load_pr_review_scorecard(project_id: str, workspace_root: Optional[str] = None) -> Optional[Dict[str, Any]]:
    return _load_json_artifact(project_id, "pr_review_scorecard.json", workspace_root)

# --- Phase 12: Final Decision + Release Archive Artifacts ---

def write_final_operator_decision(project_id: str, data: Dict[str, Any], workspace_root: Optional[str] = None) -> None:
    _write_json_artifact(project_id, "final_operator_decision.json", data, workspace_root)

def load_final_operator_decision(project_id: str, workspace_root: Optional[str] = None) -> Optional[Dict[str, Any]]:
    return _load_json_artifact(project_id, "final_operator_decision.json", workspace_root)

def write_release_manifest(project_id: str, data: Dict[str, Any], workspace_root: Optional[str] = None) -> None:
    project_dir = _resolve_project_dir(project_id, workspace_root)
    archive_dir = project_dir / "release_archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    with open(archive_dir / "release_manifest.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_release_manifest(project_id: str, workspace_root: Optional[str] = None) -> Optional[Dict[str, Any]]:
    project_dir = _resolve_project_dir(project_id, workspace_root)
    path = project_dir / "release_archive" / "release_manifest.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# --- Phase 13: Archive Index + Portfolio View Artifacts ---

def _resolve_project_factory_root(workspace_root: Optional[str] = None) -> Path:
    if not workspace_root:
        workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    workspace_path = Path(workspace_root).resolve()
    return (workspace_path / "project_outputs" / "project_factory").resolve()

def write_archive_index(data: Dict[str, Any], workspace_root: Optional[str] = None) -> None:
    root = _resolve_project_factory_root(workspace_root)
    root.mkdir(parents=True, exist_ok=True)
    with open(root / "archive_index.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_archive_index(workspace_root: Optional[str] = None) -> Optional[Dict[str, Any]]:
    root = _resolve_project_factory_root(workspace_root)
    path = root / "archive_index.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_portfolio_metrics(data: Dict[str, Any], workspace_root: Optional[str] = None) -> None:
    root = _resolve_project_factory_root(workspace_root)
    root.mkdir(parents=True, exist_ok=True)
    with open(root / "portfolio_metrics.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_portfolio_metrics(workspace_root: Optional[str] = None) -> Optional[Dict[str, Any]]:
    root = _resolve_project_factory_root(workspace_root)
    path = root / "portfolio_metrics.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# --- Phase 14: Portfolio Intelligence + Learning Memory Feedback Artifacts ---

def write_portfolio_intelligence(data: Dict[str, Any], workspace_root: Optional[str] = None) -> None:
    root = _resolve_project_factory_root(workspace_root)
    root.mkdir(parents=True, exist_ok=True)
    with open(root / "portfolio_intelligence.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_portfolio_intelligence(workspace_root: Optional[str] = None) -> Optional[Dict[str, Any]]:
    root = _resolve_project_factory_root(workspace_root)
    path = root / "portfolio_intelligence.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_learning_memory_feedback(data: Dict[str, Any], workspace_root: Optional[str] = None) -> None:
    root = _resolve_project_factory_root(workspace_root)
    root.mkdir(parents=True, exist_ok=True)
    with open(root / "learning_memory_feedback.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_learning_memory_feedback(workspace_root: Optional[str] = None) -> Optional[Dict[str, Any]]:
    root = _resolve_project_factory_root(workspace_root)
    path = root / "learning_memory_feedback.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_ceo_learning_suggestions(data: Dict[str, Any], workspace_root: Optional[str] = None) -> None:
    root = _resolve_project_factory_root(workspace_root)
    root.mkdir(parents=True, exist_ok=True)
    with open(root / "ceo_learning_suggestions.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# --- Phase 15: Portfolio Policy Autopilot Artifacts ---

def _resolve_policy_autopilot_dir(workspace_root: Optional[str] = None) -> Path:
    root = _resolve_project_factory_root(workspace_root)
    autopilot_dir = root / "policy_autopilot"
    autopilot_dir.mkdir(parents=True, exist_ok=True)
    return autopilot_dir

def write_policy_proposals(data: Dict[str, Any], workspace_root: Optional[str] = None) -> None:
    d = _resolve_policy_autopilot_dir(workspace_root)
    with open(d / "policy_proposals.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_policy_proposals(workspace_root: Optional[str] = None) -> Optional[Dict[str, Any]]:
    d = _resolve_policy_autopilot_dir(workspace_root)
    path = d / "policy_proposals.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_policy_impact_analysis(data: Dict[str, Any], workspace_root: Optional[str] = None) -> None:
    d = _resolve_policy_autopilot_dir(workspace_root)
    with open(d / "policy_impact_analysis.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_policy_impact_analysis(workspace_root: Optional[str] = None) -> Optional[Dict[str, Any]]:
    d = _resolve_policy_autopilot_dir(workspace_root)
    path = d / "policy_impact_analysis.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_policy_risk_assessment(data: Dict[str, Any], workspace_root: Optional[str] = None) -> None:
    d = _resolve_policy_autopilot_dir(workspace_root)
    with open(d / "policy_risk_assessment.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_policy_risk_assessment(workspace_root: Optional[str] = None) -> Optional[Dict[str, Any]]:
    d = _resolve_policy_autopilot_dir(workspace_root)
    path = d / "policy_risk_assessment.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_policy_suggestion_candidates(data: Dict[str, Any], workspace_root: Optional[str] = None) -> None:
    d = _resolve_policy_autopilot_dir(workspace_root)
    with open(d / "policy_suggestion_candidates.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# --- Phase 16: Policy Board & Apply Preview Artifacts ---

def write_policy_apply_preview(data: Dict[str, Any], workspace_root: Optional[str] = None) -> None:
    d = _resolve_policy_autopilot_dir(workspace_root)
    with open(d / "policy_apply_preview.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_policy_apply_preview(workspace_root: Optional[str] = None) -> Optional[Dict[str, Any]]:
    d = _resolve_policy_autopilot_dir(workspace_root)
    path = d / "policy_apply_preview.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_policy_diff_summary(content: str, workspace_root: Optional[str] = None) -> None:
    d = _resolve_policy_autopilot_dir(workspace_root)
    with open(d / "policy_diff_summary.md", "w", encoding="utf-8") as f:
        f.write(content)

def write_policy_board_package(data: Dict[str, Any], workspace_root: Optional[str] = None) -> None:
    d = _resolve_policy_autopilot_dir(workspace_root)
    with open(d / "policy_board_package.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_policy_board_package(workspace_root: Optional[str] = None) -> Optional[Dict[str, Any]]:
    d = _resolve_policy_autopilot_dir(workspace_root)
    path = d / "policy_board_package.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# --- Phase 17: Policy Draft PR Plan & Governance Evidence Artifacts ---

def write_policy_draft_pr_plan(data: Dict[str, Any], workspace_root: Optional[str] = None) -> None:
    d = _resolve_policy_autopilot_dir(workspace_root)
    with open(d / "policy_draft_pr_plan.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_policy_draft_pr_plan(workspace_root: Optional[str] = None) -> Optional[Dict[str, Any]]:
    d = _resolve_policy_autopilot_dir(workspace_root)
    path = d / "policy_draft_pr_plan.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_policy_governance_manifest(data: Dict[str, Any], workspace_root: Optional[str] = None) -> None:
    d = _resolve_policy_autopilot_dir(workspace_root)
    pack_dir = d / "policy_governance_evidence_pack"
    pack_dir.mkdir(parents=True, exist_ok=True)
    with open(pack_dir / "policy_governance_manifest.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_policy_governance_manifest(workspace_root: Optional[str] = None) -> Optional[Dict[str, Any]]:
    d = _resolve_policy_autopilot_dir(workspace_root)
    path = d / "policy_governance_evidence_pack" / "policy_governance_manifest.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# --- Phase 18: Operator-Approved Policy Draft PR Creation Artifacts ---

def write_policy_pr_creation(data: Dict[str, Any], workspace_root: Optional[str] = None) -> None:
    d = _resolve_policy_autopilot_dir(workspace_root)
    with open(d / "policy_pr_creation.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_policy_pr_creation(workspace_root: Optional[str] = None) -> Optional[Dict[str, Any]]:
    d = _resolve_policy_autopilot_dir(workspace_root)
    path = d / "policy_pr_creation.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_policy_pr_status(data: Dict[str, Any], workspace_root: Optional[str] = None) -> None:
    d = _resolve_policy_autopilot_dir(workspace_root)
    with open(d / "policy_pr_status.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_policy_pr_status(workspace_root: Optional[str] = None) -> Optional[Dict[str, Any]]:
    d = _resolve_policy_autopilot_dir(workspace_root)
    path = d / "policy_pr_status.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# --- Phase 19: Policy PR Review Gate + Verifier Mesh Artifacts ---

def write_policy_pr_review_report(data: Dict[str, Any], workspace_root: Optional[str] = None) -> None:
    d = _resolve_policy_autopilot_dir(workspace_root)
    with open(d / "policy_pr_review_report.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_policy_pr_review_report(workspace_root: Optional[str] = None) -> Optional[Dict[str, Any]]:
    d = _resolve_policy_autopilot_dir(workspace_root)
    path = d / "policy_pr_review_report.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_policy_pr_agent_review(data: Dict[str, Any], workspace_root: Optional[str] = None) -> None:
    d = _resolve_policy_autopilot_dir(workspace_root)
    with open(d / "policy_pr_agent_review.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_policy_pr_agent_review(workspace_root: Optional[str] = None) -> Optional[Dict[str, Any]]:
    d = _resolve_policy_autopilot_dir(workspace_root)
    path = d / "policy_pr_agent_review.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_policy_verifier_mesh_report(data: Dict[str, Any], workspace_root: Optional[str] = None) -> None:
    d = _resolve_policy_autopilot_dir(workspace_root)
    with open(d / "policy_verifier_mesh_report.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_policy_verifier_mesh_report(workspace_root: Optional[str] = None) -> Optional[Dict[str, Any]]:
    d = _resolve_policy_autopilot_dir(workspace_root)
    path = d / "policy_verifier_mesh_report.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# --- Phase 20: Policy Final Decision + Release Archive Artifacts ---

def write_policy_release_manifest(data: Dict[str, Any], archive_dir: Path) -> None:
    with open(archive_dir / "policy_release_manifest.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_policy_release_manifest(workspace_root: Optional[str] = None) -> Optional[Dict[str, Any]]:
    d = _resolve_policy_autopilot_dir(workspace_root)
    path = d / "policy_release_archive" / "policy_release_manifest.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_policy_learning_memory_sync(data: Dict[str, Any], archive_dir: Path) -> None:
    with open(archive_dir / "policy_learning_memory_sync.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_policy_learning_memory_sync(workspace_root: Optional[str] = None) -> Optional[Dict[str, Any]]:
    d = _resolve_policy_autopilot_dir(workspace_root)
    path = d / "policy_release_archive" / "policy_learning_memory_sync.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_policy_pr_review_scorecard(data: Dict[str, Any], workspace_root: Optional[str] = None) -> None:
    d = _resolve_policy_autopilot_dir(workspace_root)
    with open(d / "policy_pr_review_scorecard.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_policy_pr_review_scorecard(workspace_root: Optional[str] = None) -> Optional[Dict[str, Any]]:
    d = _resolve_policy_autopilot_dir(workspace_root)
    path = d / "policy_pr_review_scorecard.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
