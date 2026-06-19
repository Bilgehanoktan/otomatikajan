import os
import re
from typing import List, Dict, Set, Tuple
from services.self_repair_audit.models import AuditRunArtifact, Finding
from datetime import datetime

# Regexes
BACKEND_ROUTE_RE = re.compile(
    r'@(?:router|app)\.(get|post|put|delete|patch)\(\s*["\']([^"\']+)["\']', 
    re.IGNORECASE
)

# Common axios/fetch patterns:
# e.g., axios.get('/api/v1/ui-repair/governance/overrides')
# e.g., axios.post("/api/v1/ceo/findings")
# e.g., fetch('/api/v1/something', { method: 'POST' })
FRONTEND_AXIOS_RE = re.compile(
    r'(?:axios|client|api)\.(get|post|put|delete|patch)\(\s*["\']([^"\']+)["\']',
    re.IGNORECASE
)

FRONTEND_FETCH_RE = re.compile(
    r'fetch\(\s*["\']([^"\']+)["\']',
    re.IGNORECASE
)

class APIContractScanner:
    def __init__(self, workspace_root: str):
        self.workspace_root = workspace_root
        self.frontend_dir = os.path.join(workspace_root, "apps", "refine_control_plane", "src")
        self.backend_dir = os.path.join(workspace_root, "services", "workflow_api")

    def scan(self, audit_run_id: str) -> AuditRunArtifact:
        findings: List[Finding] = []
        evidence_refs: List[str] = []

        # 1. Parse Backend Routes
        # Maps path -> set of allowed uppercase methods
        backend_routes: Dict[str, Set[str]] = {}
        
        if os.path.exists(self.backend_dir):
            for root, _, files in os.walk(self.backend_dir):
                for file in files:
                    if file.endswith(".py"):
                        path = os.path.join(root, file)
                        evidence_refs.append(f"backend:{os.path.relpath(path, self.workspace_root)}")
                        try:
                            with open(path, "r", encoding="utf-8") as f:
                                content = f.read()
                                for match in BACKEND_ROUTE_RE.finditer(content):
                                    method = match.group(1).upper()
                                    route_path = match.group(2)
                                    
                                    # Normalize route (e.g. resolve path parameters or trailing slashes)
                                    normalized_path = self._normalize_route(route_path)
                                    backend_routes.setdefault(normalized_path, set()).add(method)
                        except Exception as e:
                            pass

        # 2. Parse Frontend Calls
        # Maps (path, method) -> list of files where it was seen
        frontend_calls: Dict[Tuple[str, str], List[str]] = {}

        if os.path.exists(self.frontend_dir):
            for root, _, files in os.walk(self.frontend_dir):
                for file in files:
                    if file.endswith((".js", ".jsx", ".ts", ".tsx")):
                        path = os.path.join(root, file)
                        rel_path = os.path.relpath(path, self.workspace_root)
                        evidence_refs.append(f"frontend:{rel_path}")
                        try:
                            with open(path, "r", encoding="utf-8") as f:
                                content = f.read()
                                
                                # Axios-style matches
                                for match in FRONTEND_AXIOS_RE.finditer(content):
                                    method = match.group(1).upper()
                                    route_path = match.group(2)
                                    if route_path.startswith("/api/"):
                                        norm_path = self._normalize_route(route_path)
                                        frontend_calls.setdefault((norm_path, method), []).append(rel_path)
                                
                                # Fetch-style matches
                                for match in FRONTEND_FETCH_RE.finditer(content):
                                    route_path = match.group(1)
                                    if route_path.startswith("/api/"):
                                        norm_path = self._normalize_route(route_path)
                                        # Determine method by looking ahead in the next 100 characters for method: 'POST' etc.
                                        start_pos = match.end()
                                        snippet = content[start_pos:start_pos+120]
                                        method_match = re.search(r'method\s*:\s*["\'](GET|POST|PUT|DELETE|PATCH)["\']', snippet, re.IGNORECASE)
                                        method = method_match.group(1).upper() if method_match else "GET"
                                        
                                        frontend_calls.setdefault((norm_path, method), []).append(rel_path)
                        except Exception as e:
                            pass

        # 3. Analyze Mismatches
        finding_count = 0
        for (f_path, f_method), files in frontend_calls.items():
            if f_path not in backend_routes:
                finding_count += 1
                findings.append(Finding(
                    finding_id=f"AUD-FIND-API-{finding_count:03d}",
                    title="Missing API Route Mismatch",
                    description=f"Frontend calls non-existent backend route '{f_path}' using method {f_method}.",
                    category="api_contract",
                    severity="HIGH",
                    priority_score=83,
                    source="api_contract_scanner",
                    affected_files=list(set(files)),
                    affected_endpoints=[f_path],
                    recommended_action=f"Define endpoint '{f_path}' with method {f_method} in backend router.",
                    suggested_workflow="self_repair_v1",
                    requires_human_approval=True,
                    evidence_refs=[f"frontend_call:{f_method} {f_path}"]
                ))
            else:
                allowed_methods = backend_routes[f_path]
                if f_method not in allowed_methods:
                    finding_count += 1
                    findings.append(Finding(
                        finding_id=f"AUD-FIND-API-{finding_count:03d}",
                        title="API Method Mismatch",
                        description=f"Frontend calls backend route '{f_path}' with method {f_method}, but backend only supports: {', '.join(allowed_methods)}.",
                        category="api_contract",
                        severity="HIGH",
                        priority_score=85,
                        source="api_contract_scanner",
                        affected_files=list(set(files)),
                        affected_endpoints=[f_path],
                        recommended_action=f"Update backend endpoint '{f_path}' or frontend call to align HTTP methods.",
                        suggested_workflow="self_repair_v1",
                        requires_human_approval=True,
                        evidence_refs=[f"method_mismatch:{f_method} vs {allowed_methods}"]
                    ))

        status = "PASSED"
        if any(f.severity in {"CRITICAL", "HIGH"} for f in findings):
            status = "FAILED"
        elif findings:
            status = "WARNING"

        return AuditRunArtifact(
            audit_run_id=audit_run_id,
            scanner="api_contract_scanner",
            status=status,
            findings=findings,
            evidence_refs=evidence_refs,
            created_at=datetime.now().isoformat()
        )

    def _normalize_route(self, route: str) -> str:
        """
        Normalizes paths (resolves parameters, removes trailing slashes).
        e.g., /api/v1/user/{id} -> /api/v1/user/:param
        e.g., /api/v1/user/:id/ -> /api/v1/user/:param
        """
        # Strip trailing slash
        route = route.rstrip("/")
        # Resolve query parameters
        if "?" in route:
            route = route.split("?")[0]
        # Replace variable path parameters: {id} or :id or {project_id}
        route = re.sub(r'\{[^}]+\}', ':param', route)
        route = re.sub(r':[a-zA-Z0-9_]+', ':param', route)
        return route
