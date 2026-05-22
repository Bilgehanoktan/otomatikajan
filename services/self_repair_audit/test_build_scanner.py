import os
from typing import List
from services.self_repair_audit.models import AuditRunArtifact, Finding
from datetime import datetime

class TestBuildScanner:
    def __init__(self, workspace_root: str):
        self.workspace_root = workspace_root

    def scan(self, audit_run_id: str) -> AuditRunArtifact:
        findings: List[Finding] = []
        evidence_refs: List[str] = []

        # Checklists definition: (Description, relative path(s) to search, severity)
        checks = [
            ("Pytest Configuration", ["pytest.ini"], "HIGH"),
            ("Workspace package.json", ["package.json"], "HIGH"),
            ("Next.js Configuration", [
                "apps/refine_control_plane/next.config.ts",
                "apps/refine_control_plane/next.config.js",
                "apps/refine_control_plane/next.config.mjs"
            ], "HIGH"),
            ("Self-Repair Workflow YAML", [
                "workflows/self_repair_v1.yaml",
                "workflows/self_repair_audit_v1.yaml"
            ], "CRITICAL")
        ]

        finding_count = 0
        for name, rel_paths, severity in checks:
            found = False
            scanned_paths = []
            for rel_path in rel_paths:
                full_path = os.path.join(self.workspace_root, rel_path)
                scanned_paths.append(rel_path)
                if os.path.exists(full_path):
                    found = True
                    evidence_refs.append(f"config_exists:{rel_path}")
                    break
            
            if not found:
                finding_count += 1
                findings.append(Finding(
                    finding_id=f"AUD-FIND-BUILD-{finding_count:03d}",
                    title=f"Missing Critical {name}",
                    description=f"Could not locate required config file. Tried searching for: {', '.join(scanned_paths)}.",
                    category="test_build",
                    severity=severity,
                    priority_score=90 if severity == "CRITICAL" else 75,
                    source="test_build_scanner",
                    recommended_action=f"Create a standard '{scanned_paths[0]}' configuration file inside the designated folder.",
                    suggested_workflow="self_repair_v1"
                ))

        status = "PASSED"
        if any(f.severity in {"CRITICAL", "HIGH"} for f in findings):
            status = "FAILED"
        elif findings:
            status = "WARNING"

        return AuditRunArtifact(
            audit_run_id=audit_run_id,
            scanner="test_build_scanner",
            status=status,
            findings=findings,
            evidence_refs=evidence_refs,
            created_at=datetime.now().isoformat()
        )
