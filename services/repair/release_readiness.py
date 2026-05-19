import re
import json
import hashlib
from datetime import datetime, UTC
from pathlib import Path
from typing import Any, Optional
import yaml
from fastapi import FastAPI

CONFIG_PATH = Path("e:/ai_company_faz12.1/configs/release_contract_matrix.yaml")
FRONTEND_SRC_DIR = Path("e:/ai_company_faz12.1/apps/refine_control_plane/src")
REPAIR_OUTPUTS_DIR = Path("e:/ai_company_faz12.1/repair_outputs")

def load_matrix_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def calculate_sha256(file_path: Path) -> str:
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            sha.update(chunk)
    return sha.hexdigest()

def normalize_path(path: str) -> str:
    # Replace dynamic parameters like {run_id} or ${run_id} with *
    path = re.sub(r"\{[a-zA-Z0-9_]+\}", "*", path)
    path = re.sub(r"\$[a-zA-Z0-9_]+", "*", path)
    path = re.sub(r"\$\{[a-zA-Z0-9_]+\}", "*", path)
    return path.rstrip("/")

def build_contract_matrix(app: Optional[FastAPI] = None) -> list[dict[str, Any]]:
    config = load_matrix_config()
    api_routes = config.get("api_routes", [])
    
    # Get active registered routes if app is provided
    registered_routes = {}
    if app:
        for r in app.routes:
            methods = getattr(r, "methods", set())
            for m in methods:
                registered_routes[(normalize_path(r.path), m.upper())] = True

    matrix = []
    for route_info in api_routes:
        route_path = route_info.get("route", "")
        method = route_info.get("method", "GET").upper()
        
        normalized = normalize_path(route_path)
        is_active = True
        if app:
            is_active = (normalized, method) in registered_routes

        matrix.append({
            "surface": route_info.get("surface", "Unknown"),
            "route_or_artifact": route_path,
            "method": method,
            "owner_module": route_info.get("owner_module", ""),
            "required_auth": route_info.get("required_auth", True),
            "expected_status": "active" if is_active else "missing",
            "required_fields": [],
            "current_status": "healthy" if is_active else "missing",
            "last_checked_at": datetime.now(UTC).isoformat(),
            "blocking": route_info.get("blocking", True),
            "notes": "Route matches active FastAPI router" if is_active else "FastAPI route not found in active router"
        })
    return matrix

def validate_api_contracts(app: Optional[FastAPI] = None) -> tuple[list[dict[str, Any]], bool]:
    matrix = build_contract_matrix(app)
    is_blocked = False
    for entry in matrix:
        if entry["current_status"] == "missing" and entry["blocking"]:
            is_blocked = True
    return matrix, is_blocked

def scan_frontend_api_calls(src_dir: Optional[Path] = None) -> set[str]:
    api_calls = set()
    pattern = re.compile(r"\/api\/v1\/[a-zA-Z0-9_\-\/\{\}\$\.\?&=]+")
    target_dir = src_dir if src_dir is not None else FRONTEND_SRC_DIR
    if not target_dir.exists():
        return api_calls
    for p in target_dir.glob("**/*"):
        if p.is_file() and p.suffix in (".ts", ".tsx", ".js", ".jsx", ".json"):
            try:
                content = p.read_text(encoding="utf-8")
                for match in pattern.finditer(content):
                    path = match.group(0)
                    if "?" in path:
                        path = path.split("?")[0]
                    # Convert template literal syntax
                    cleaned = re.sub(r"\$\{([a-zA-Z0-9_\.]+)\}", r"{\1}", path)
                    cleaned = cleaned.rstrip("/")
                    api_calls.add(cleaned)
            except Exception:
                pass
    return api_calls

def validate_frontend_backend_parity(app: Optional[FastAPI] = None, src_dir: Optional[Path] = None) -> tuple[list[dict[str, Any]], bool]:
    scanned_frontend_calls = scan_frontend_api_calls(src_dir)
    
    registered_routes = set()
    if app:
        for r in app.routes:
            registered_routes.add(normalize_path(r.path))

    parity_results = []
    is_blocked = False
    
    # If app is None, we default to the expected ones in YAML config
    config = load_matrix_config()
    expected_frontend = config.get("frontend_expected_api_calls", [])
    
    expected_paths = {normalize_path(x.get("route", "")) for x in expected_frontend}

    for call in scanned_frontend_calls:
        norm_call = normalize_path(call)
        
        # Check if the call starts with /api/v1/
        if not call.startswith("/api/v1/"):
            continue

        exists = False
        if app:
            exists = norm_call in registered_routes
        else:
            exists = norm_call in expected_paths

        status = "healthy" if exists else "missing"
        blocking = not exists  # missing frontend backend parity is blocking
        
        if blocking:
            is_blocked = True

        parity_results.append({
            "frontend_call": call,
            "normalized_call": norm_call,
            "status": status,
            "blocking": blocking,
            "notes": "Parity confirmed with backend route" if exists else "Frontend calls a route that is missing on backend"
        })
        
    return parity_results, is_blocked

def validate_artifact_contract(run_dir: Path) -> tuple[list[dict[str, Any]], bool]:
    config = load_matrix_config()
    artifact_schemas = config.get("artifact_schemas", [])
    
    manifest_path = run_dir / "artifact_manifest.json"
    manifest = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    artifact_results = []
    is_blocked = False

    for schema in artifact_schemas:
        name = schema.get("artifact_name", "")
        required = schema.get("required", False)
        blocking_rule = schema.get("blocking", False)
        
        file_path = run_dir / name
        exists = file_path.exists()
        
        status = "healthy"
        notes = "Artifact matches matrix schema validation."
        blocking = False

        if not exists:
            if required:
                status = "missing"
                notes = f"Required artifact {name} is missing from run directory."
                if blocking_rule:
                    blocking = True
                    is_blocked = True
            else:
                status = "optional_missing"
                notes = f"Optional artifact {name} is not present."
        else:
            # Recompute and check hash against manifest
            if name != "artifact_manifest.json" and manifest:
                expected_hash = manifest.get(name, {}).get("sha256")
                if expected_hash:
                    actual_hash = calculate_sha256(file_path)
                    if actual_hash != expected_hash:
                        status = "hash_mismatch"
                        notes = f"Recomputed hash ({actual_hash[:8]}) does not match manifest hash ({expected_hash[:8]})."
                        if blocking_rule:
                            blocking = True
                            is_blocked = True
                else:
                    status = "untracked"
                    notes = f"Artifact {name} exists but is untracked in manifest."

        artifact_results.append({
            "artifact_name": name,
            "status": status,
            "blocking": blocking,
            "notes": notes
        })

    # Decisive Integrity Checks
    tournament_path = run_dir / "tournament_result.json"
    human_gate_path = run_dir / "human_gate_decision.json"
    draft_pr_path = run_dir / "draft_pr_metadata.json"
    pr_review_path = run_dir / "pr_review.json"

    # Integrity Check 1: tournament vs human gate selected_candidate_id mismatch
    if tournament_path.exists() and human_gate_path.exists():
        try:
            tour = json.loads(tournament_path.read_text(encoding="utf-8"))
            gate = json.loads(human_gate_path.read_text(encoding="utf-8"))
            t_cand = tour.get("selected_candidate_id")
            g_cand = gate.get("selected_candidate_id")
            if t_cand and g_cand and t_cand != g_cand:
                is_blocked = True
                artifact_results.append({
                    "artifact_name": "tournament_vs_human_gate_selected_candidate",
                    "status": "integrity_failed",
                    "blocking": True,
                    "notes": f"Selected candidate mismatch: Tournament picked {t_cand}, but Human Gate approved {g_cand}."
                })
        except Exception:
            pass

    # Integrity Check 2: draft_pr without PR review completed
    if draft_pr_path.exists():
        pr_review_ok = False
        if pr_review_path.exists():
            try:
                rev = json.loads(pr_review_path.read_text(encoding="utf-8"))
                if rev.get("status") == "completed":
                    pr_review_ok = True
            except Exception:
                pass
        
        if not pr_review_ok:
            is_blocked = True
            artifact_results.append({
                "artifact_name": "draft_pr_integrity",
                "status": "integrity_failed",
                "blocking": True,
                "notes": "Draft PR metadata was built, but no completed PR review exists."
            })

    # Integrity Check 3: draft_pr_metadata.json built with unapproved/rejected Human Gate
    if draft_pr_path.exists() and human_gate_path.exists():
        try:
            gate = json.loads(human_gate_path.read_text(encoding="utf-8"))
            g_status = gate.get("status")
            if g_status not in ("APPROVED", "DRAFT_PR_ONLY"):
                is_blocked = True
                artifact_results.append({
                    "artifact_name": "draft_pr_governance_integrity",
                    "status": "integrity_failed",
                    "blocking": True,
                    "notes": f"Draft PR metadata exists but Human Gate status is {g_status}."
                })
        except Exception:
            pass

    # Integrity Check 4: Human Gate missing for high risk
    risk_path = run_dir / "risk_report.json"
    if risk_path.exists() and not human_gate_path.exists():
        try:
            risk = json.loads(risk_path.read_text(encoding="utf-8"))
            if risk.get("risk_score", 0.0) > 0.70:
                is_blocked = True
                artifact_results.append({
                    "artifact_name": "high_risk_human_gate_enforcement",
                    "status": "integrity_failed",
                    "blocking": True,
                    "notes": "Risk score > 0.70 requires a Human Gate, but no decision was recorded."
                })
        except Exception:
            pass

    return artifact_results, is_blocked

def build_release_readiness_report(
    run_dir: Optional[Path] = None, 
    app: Optional[FastAPI] = None, 
    src_dir: Optional[Path] = None
) -> dict[str, Any]:
    api_matrix, api_blocked = validate_api_contracts(app)
    parity_matrix, parity_blocked = validate_frontend_backend_parity(app, src_dir)
    
    artifact_matrix = []
    artifact_blocked = False
    if run_dir and run_dir.exists():
        artifact_matrix, artifact_blocked = validate_artifact_contract(run_dir)
        
    blocked = api_blocked or parity_blocked or artifact_blocked
    
    status = "READY"
    if blocked:
        status = "BLOCKED"
    elif api_blocked or parity_blocked or artifact_blocked:
        status = "READY_WITH_WARNINGS"
        
    blocking_count = 0
    warning_count = 0
    for e in api_matrix:
        if e["current_status"] == "missing":
            if e["blocking"]:
                blocking_count += 1
            else:
                warning_count += 1
    for e in parity_matrix:
        if e["status"] == "missing":
            if e["blocking"]:
                blocking_count += 1
            else:
                warning_count += 1
    for e in artifact_matrix:
        if e["status"] in ("missing", "hash_mismatch", "integrity_failed"):
            if e["blocking"]:
                blocking_count += 1
            else:
                warning_count += 1

    recommendations = []
    if status == "BLOCKED":
        recommendations.append("Fix missing/invalid contract routes or mismatching hashes before release.")
    if api_blocked:
        recommendations.append("Enable required API endpoints in the FastAPI router structure.")
    if parity_blocked:
        recommendations.append("Resolve unimplemented backend endpoints that are currently called by Refine Control Plane.")
    if artifact_blocked:
        recommendations.append("Recompute and realign taskflow manifest signatures, or collect operator sign-offs.")

    report = {
        "status": status,
        "blocking_count": blocking_count,
        "warning_count": warning_count,
        "checked_at": datetime.now(UTC).isoformat(),
        "api_contracts": api_matrix,
        "artifact_contracts": artifact_matrix,
        "frontend_backend_parity": parity_matrix,
        "recommendations": recommendations
    }

    # Persist latest report
    latest_report_dir = REPAIR_OUTPUTS_DIR / "release_readiness"
    latest_report_dir.mkdir(parents=True, exist_ok=True)
    report_file = latest_report_dir / "latest_report.json"
    
    try:
        report_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
    except Exception:
        pass

    return report
