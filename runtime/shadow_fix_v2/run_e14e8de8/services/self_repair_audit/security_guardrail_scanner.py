import os
import re
import yaml
from typing import List
from services.self_repair_audit.models import AuditRunArtifact, Finding
from datetime import datetime

class SecurityGuardrailScanner:
    def __init__(self, workspace_root: str):
        self.workspace_root = workspace_root
        self.autonomy_policy_path = os.path.join(workspace_root, "configs", "autonomy_policy.yaml")
        self.external_catalog_path = os.path.join(workspace_root, "configs", "external_project_agent_matrix.yaml")
        # Fallback to external_agent_catalog if the project matrix doesn't exist yet
        self.legacy_catalog_path = os.path.join(workspace_root, "configs", "external_agent_catalog.yaml")

    def scan(self, audit_run_id: str) -> AuditRunArtifact:
        findings: List[Finding] = []
        evidence_refs: List[str] = []
        finding_count = 0

        # 1. Verify Autonomy Policies
        if os.path.exists(self.autonomy_policy_path):
            evidence_refs.append("policy:autonomy_policy.yaml")
            try:
                with open(self.autonomy_policy_path, "r", encoding="utf-8") as f:
                    policy = yaml.safe_load(f)
                    
                global_level = policy.get("current_global_level", "L1")
                # L4 means fully autonomous bypassing human gate on everything
                if global_level == "L4":
                    finding_count += 1
                    findings.append(Finding(
                        finding_id=f"AUD-FIND-SEC-{finding_count:03d}",
                        title="Unrestricted Autonomy Level Active",
                        description="Global autonomy level is configured to L4, which allows auto-execution without human gates.",
                        category="security",
                        severity="CRITICAL",
                        priority_score=98,
                        source="security_guardrail_scanner",
                        affected_files=["configs/autonomy_policy.yaml"],
                        recommended_action="Downgrade global level to L3 or L2, enforcing human approval overrides.",
                        suggested_workflow="self_repair_v1"
                    ))
            except Exception as e:
                pass

        # 2. Verify Forbidden Actions on External Tools
        catalog_to_check = self.external_catalog_path if os.path.exists(self.external_catalog_path) else self.legacy_catalog_path
        if os.path.exists(catalog_to_check):
            evidence_refs.append(f"policy:{os.path.basename(catalog_to_check)}")
            try:
                with open(catalog_to_check, "r", encoding="utf-8") as f:
                    catalog = yaml.safe_load(f)
                
                # Check within external_agents (legacy) or integration_matrix (new)
                agents_data = catalog.get("external_agents", catalog.get("integration_matrix", {}))
                
                for agent_key, agent_meta in agents_data.items():
                    forbidden = agent_meta.get("forbidden_actions", [])
                    
                    # Ensure direct_git_push and bypass_human_gate are forbidden
                    for action in ["direct_git_push", "bypass_human_gate"]:
                        if action not in forbidden:
                            finding_count += 1
                            findings.append(Finding(
                                finding_id=f"AUD-FIND-SEC-{finding_count:03d}",
                                title="Missing External Agent Sandbox Forbidden Action",
                                description=f"External agent '{agent_key}' does not restrict '{action}' in its forbidden_actions list.",
                                category="security",
                                severity="HIGH",
                                priority_score=85,
                                source="security_guardrail_scanner",
                                affected_files=[os.path.relpath(catalog_to_check, self.workspace_root)],
                                recommended_action=f"Add '{action}' to forbidden_actions in the agent config catalog.",
                                suggested_workflow="self_repair_v1"
                            ))
            except Exception as e:
                pass

        # 3. Check for potential raw password logging patterns in source files (e.g. console.log(password))
        # Walk a subset of apps to check if they print tokens
        apps_dir = os.path.join(self.workspace_root, "apps", "refine_control_plane", "src")
        if os.path.exists(apps_dir):
            raw_log_pattern = re.compile(r'console\.log\([^)]*(?:password|token|secret|api_key|apikey)[^)]*\)', re.IGNORECASE)
            for root, _, files in os.walk(apps_dir):
                for file in files:
                    if file.endswith((".js", ".jsx", ".ts", ".tsx")):
                        path = os.path.join(root, file)
                        try:
                            with open(path, "r", encoding="utf-8") as f:
                                content = f.read()
                                if raw_log_pattern.search(content):
                                    finding_count += 1
                                    rel_file = os.path.relpath(path, self.workspace_root)
                                    findings.append(Finding(
                                        finding_id=f"AUD-FIND-SEC-{finding_count:03d}",
                                        title="Sensitive Key Logging Detected",
                                        description=f"Source file '{rel_file}' may be logging credentials or secrets via console.log.",
                                        category="security",
                                        severity="MEDIUM",
                                        priority_score=54,
                                        source="security_guardrail_scanner",
                                        affected_files=[rel_file],
                                        recommended_action="Remove or scrub sensitive print statements in client-side code.",
                                        suggested_workflow="self_repair_v1"
                                    ))
                        except Exception:
                            pass

        status = "PASSED"
        if any(f.severity in {"CRITICAL", "HIGH"} for f in findings):
            status = "FAILED"
        elif findings:
            status = "WARNING"

        return AuditRunArtifact(
            audit_run_id=audit_run_id,
            scanner="security_guardrail_scanner",
            status=status,
            findings=findings,
            evidence_refs=evidence_refs,
            created_at=datetime.now().isoformat()
        )
