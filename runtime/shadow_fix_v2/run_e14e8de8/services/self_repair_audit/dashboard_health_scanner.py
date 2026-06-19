import os
from typing import List
from services.self_repair_audit.models import AuditRunArtifact, Finding
from datetime import datetime

class DashboardHealthScanner:
    def __init__(self, workspace_root: str):
        self.workspace_root = workspace_root
        self.app_dir = os.path.join(workspace_root, "apps", "refine_control_plane", "src", "app")

    def scan(self, audit_run_id: str) -> AuditRunArtifact:
        findings: List[Finding] = []
        evidence_refs: List[str] = []

        # Target routes and their expected subfolders in src/app/
        # (Route URL path, Relative folder path under src/app/)
        target_routes = [
            ("/", ""),
            ("/workflows", "workflows"),
            ("/repair-lab", "repair-lab"),
            ("/system-health", "system-health"),
            ("/ui-repair", "ui-repair"),
            ("/governance/incidents", "governance/incidents")
        ]

        if not os.path.exists(self.app_dir):
            findings.append(Finding(
                finding_id="AUD-FIND-DASH-000",
                title="Frontend App Router Missing",
                description=f"The main Next.js App Router directory '{self.app_dir}' was not found.",
                category="dashboard_health",
                severity="CRITICAL",
                priority_score=99,
                source="dashboard_health_scanner",
                recommended_action="Ensure the Next.js refine_control_plane workspace is properly checked out.",
                suggested_workflow="self_repair_v1"
            ))
        else:
            evidence_refs.append(f"app_router_root:{os.path.relpath(self.app_dir, self.workspace_root)}")
            
            finding_count = 0
            for route_url, rel_folder in target_routes:
                route_dir = os.path.join(self.app_dir, rel_folder) if rel_folder else self.app_dir
                
                # We check for standard Next.js entrypoint files: page.tsx, page.js, page.jsx, page.ts, route.ts, route.js
                possible_entrypoints = ["page.tsx", "page.js", "page.jsx", "page.ts", "route.ts", "route.js"]
                found_entry = False
                
                if os.path.exists(route_dir) and os.path.isdir(route_dir):
                    evidence_refs.append(f"route_folder:{route_url}")
                    for entry in possible_entrypoints:
                        if os.path.exists(os.path.join(route_dir, entry)):
                            found_entry = True
                            break
                
                # Handle special case where /governance/incidents might be structured as /incidents
                if not found_entry and route_url == "/governance/incidents":
                    alt_dir = os.path.join(self.app_dir, "incidents")
                    if os.path.exists(alt_dir) and os.path.isdir(alt_dir):
                        for entry in possible_entrypoints:
                            if os.path.exists(os.path.join(alt_dir, entry)):
                                found_entry = True
                                break

                if not found_entry:
                    finding_count += 1
                    findings.append(Finding(
                        finding_id=f"AUD-FIND-DASH-{finding_count:03d}",
                        title="Missing Dashboard Page Entrypoint",
                        description=f"Dashboard route '{route_url}' does not contain any valid Next.js page or route entrypoint in target directory.",
                        category="dashboard_health",
                        severity="HIGH" if route_url in ["/", "/workflows"] else "MEDIUM",
                        priority_score=80 if route_url in ["/", "/workflows"] else 50,
                        source="dashboard_health_scanner",
                        affected_files=[os.path.relpath(route_dir, self.workspace_root)] if os.path.exists(route_dir) else [],
                        recommended_action=f"Create a 'page.tsx' file under the '{rel_folder}' folder in your App Router.",
                        suggested_workflow="self_repair_v1"
                    ))

        status = "PASSED"
        if any(f.severity in {"CRITICAL", "HIGH"} for f in findings):
            status = "FAILED"
        elif findings:
            status = "WARNING"

        return AuditRunArtifact(
            audit_run_id=audit_run_id,
            scanner="dashboard_health_scanner",
            status=status,
            findings=findings,
            evidence_refs=evidence_refs,
            created_at=datetime.now().isoformat()
        )
