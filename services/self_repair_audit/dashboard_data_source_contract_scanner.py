import os
from datetime import datetime
from typing import List

from services.self_repair_audit.models import AuditRunArtifact, Finding


class DashboardDataSourceContractScanner:
    """
    Checks high-risk operational dashboard pages against their canonical API sources.

    This is intentionally static and report-only. It catches pages that render operational
    readiness from stale/generic resources or hardcoded success labels.
    """

    CONTRACTS = [
        {
            "route": "/ops/launch-gates",
            "file": os.path.join("apps", "refine_control_plane", "src", "app", "ops", "launch-gates", "page.tsx"),
            "required_source": "/governance/ops/launch-gates",
            "forbidden_sources": ["governance/validations"],
            "forbidden_literals": [],
        },
        {
            "route": "/ops/handover-status",
            "file": os.path.join("apps", "refine_control_plane", "src", "app", "ops", "handover-status", "page.tsx"),
            "required_source": "/governance/ops/handover-status",
            "forbidden_sources": ["governance/signoffs"],
            "forbidden_literals": ["100% NOMINAL", "01 ACTIVE"],
        },
    ]

    def __init__(self, workspace_root: str):
        self.workspace_root = workspace_root

    def scan(self, audit_run_id: str) -> AuditRunArtifact:
        findings: List[Finding] = []
        evidence_refs: List[str] = []

        for idx, contract in enumerate(self.CONTRACTS, start=1):
            path = os.path.join(self.workspace_root, contract["file"])
            rel_path = os.path.relpath(path, self.workspace_root)
            evidence_refs.append(f"dashboard_contract:{contract['route']}:{rel_path}")

            if not os.path.exists(path):
                findings.append(Finding(
                    finding_id=f"AUD-FIND-DASH-DS-{idx:03d}",
                    title="Missing Operational Dashboard Contract File",
                    description=f"Operational dashboard route '{contract['route']}' is missing expected file '{rel_path}'.",
                    category="dashboard_health",
                    severity="HIGH",
                    priority_score=80,
                    source="dashboard_data_source_contract_scanner",
                    affected_files=[rel_path],
                    recommended_action=f"Create the route file and bind it to canonical source '{contract['required_source']}'.",
                    suggested_workflow="self_repair_v1",
                    requires_human_approval=True,
                ))
                continue

            with open(path, "r", encoding="utf-8") as handle:
                content = handle.read()

            if contract["required_source"] not in content:
                findings.append(Finding(
                    finding_id=f"AUD-FIND-DASH-DS-{idx:03d}",
                    title="Operational Dashboard Missing Canonical Data Source",
                    description=(
                        f"Operational dashboard route '{contract['route']}' does not read canonical source "
                        f"'{contract['required_source']}'."
                    ),
                    category="dashboard_health",
                    severity="HIGH",
                    priority_score=82,
                    source="dashboard_data_source_contract_scanner",
                    affected_files=[rel_path],
                    affected_endpoints=[contract["required_source"]],
                    recommended_action=f"Bind '{contract['route']}' to '{contract['required_source']}' and compute status from live response.",
                    suggested_workflow="self_repair_v1",
                    requires_human_approval=True,
                    evidence_refs=[f"missing_source:{contract['required_source']}"],
                ))

            for forbidden in contract["forbidden_sources"]:
                if forbidden in content:
                    findings.append(Finding(
                        finding_id=f"AUD-FIND-DASH-DS-{idx:03d}-{len(findings)+1:02d}",
                        title="Operational Dashboard Uses Non-Canonical Data Source",
                        description=(
                            f"Operational dashboard route '{contract['route']}' still reads non-canonical source "
                            f"'{forbidden}'."
                        ),
                        category="dashboard_health",
                        severity="HIGH",
                        priority_score=83,
                        source="dashboard_data_source_contract_scanner",
                        affected_files=[rel_path],
                        recommended_action=f"Remove '{forbidden}' as the operational readiness source for '{contract['route']}'.",
                        suggested_workflow="self_repair_v1",
                        requires_human_approval=True,
                        evidence_refs=[f"forbidden_source:{forbidden}"],
                    ))

            for literal in contract["forbidden_literals"]:
                if literal in content:
                    findings.append(Finding(
                        finding_id=f"AUD-FIND-DASH-DS-{idx:03d}-{len(findings)+1:02d}",
                        title="Operational Dashboard Hardcodes Success State",
                        description=(
                            f"Operational dashboard route '{contract['route']}' hardcodes success literal "
                            f"'{literal}' instead of deriving it from live API state."
                        ),
                        category="dashboard_health",
                        severity="MEDIUM",
                        priority_score=55,
                        source="dashboard_data_source_contract_scanner",
                        affected_files=[rel_path],
                        recommended_action=f"Compute '{literal}' equivalent from '{contract['required_source']}' response fields.",
                        suggested_workflow="self_repair_v1",
                        requires_human_approval=True,
                        evidence_refs=[f"hardcoded_success:{literal}"],
                    ))

        status = "PASSED"
        if any(f.severity in {"CRITICAL", "HIGH"} for f in findings):
            status = "FAILED"
        elif findings:
            status = "WARNING"

        return AuditRunArtifact(
            audit_run_id=audit_run_id,
            scanner="dashboard_data_source_contract_scanner",
            status=status,
            findings=findings,
            evidence_refs=evidence_refs,
            created_at=datetime.now().isoformat(),
        )
