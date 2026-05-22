import os
from typing import List
from services.self_repair_audit.models import AuditRunArtifact, Finding
from datetime import datetime

class ProjectFactoryReadinessScanner:
    def __init__(self, workspace_root: str):
        self.workspace_root = workspace_root

    def scan(self, audit_run_id: str) -> AuditRunArtifact:
        findings: List[Finding] = []
        evidence_refs: List[str] = []

        # List of required project factory files/directories
        required_paths = [
            ("workflows/project_factory_v1.yaml", "file"),
            ("configs/project_factory_contract.yaml", "file"),
            ("generated_projects/.gitkeep", "file"),
            ("project_outputs/.gitkeep", "file"),
            ("services/project_factory/", "dir")
        ]

        finding_count = 0
        for path, path_type in required_paths:
            full_path = os.path.join(self.workspace_root, path)
            exists = os.path.exists(full_path)
            
            if exists:
                # Double check the type
                if path_type == "file" and os.path.isfile(full_path):
                    evidence_refs.append(f"factory_path_ok:{path}")
                elif path_type == "dir" and os.path.isdir(full_path):
                    evidence_refs.append(f"factory_path_ok:{path}")
                else:
                    finding_count += 1
                    findings.append(Finding(
                        finding_id=f"AUD-FIND-PF-{finding_count:03d}",
                        title="Invalid Project Factory Component Type",
                        description=f"Expected '{path}' to be a {path_type}, but found mismatching filesystem type.",
                        category="project_factory",
                        severity="MEDIUM",
                        priority_score=45,
                        source="project_factory_readiness_scanner",
                        affected_files=[path],
                        recommended_action=f"Ensure '{path}' conforms to expected type: {path_type}.",
                        suggested_workflow="self_repair_v1"
                    ))
            else:
                finding_count += 1
                findings.append(Finding(
                    finding_id=f"AUD-FIND-PF-{finding_count:03d}",
                    title="Missing Project Factory Component",
                    description=f"Project Factory prerequisite '{path}' was not found in the workspace.",
                    category="project_factory",
                    severity="MEDIUM",
                    priority_score=41,
                    source="project_factory_readiness_scanner",
                    affected_files=[path],
                    recommended_action=f"Create the missing Project Factory scaffold component '{path}'.",
                    suggested_workflow="self_repair_v1"
                ))

        status = "PASSED"
        if findings:
            status = "WARNING"  # Since they are all MEDIUM severity

        return AuditRunArtifact(
            audit_run_id=audit_run_id,
            scanner="project_factory_readiness_scanner",
            status=status,
            findings=findings,
            evidence_refs=evidence_refs,
            created_at=datetime.now().isoformat()
        )
