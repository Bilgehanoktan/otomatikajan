import os
import sys
import uuid
import subprocess
from datetime import datetime
from typing import List, Dict, Any

from services.self_repair_audit.models import Finding, AuditRunArtifact
from services.self_repair_audit.artifacts import save_artifact
from services.self_repair_audit.finding_classifier import classify_findings

# Scanners
from services.self_repair_audit.api_contract_scanner import APIContractScanner
from services.self_repair_audit.dashboard_data_source_contract_scanner import DashboardDataSourceContractScanner
from services.self_repair_audit.dashboard_health_scanner import DashboardHealthScanner
from services.self_repair_audit.test_build_scanner import TestBuildScanner
from services.self_repair_audit.security_guardrail_scanner import SecurityGuardrailScanner
from services.self_repair_audit.project_factory_readiness_scanner import ProjectFactoryReadinessScanner

class AuditOrchestrator:
    def __init__(self, workspace_root: str = None):
        if not workspace_root:
            # Resolve root directory: e:\ai_company_faz12.1
            self.workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        else:
            self.workspace_root = workspace_root

    def generate_run_id(self) -> str:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return f"AUD-{timestamp}"

    def collect_system_context(self, audit_run_id: str) -> Dict[str, Any]:
        """
        Gathers environment-level read-only context.
        """
        git_branch = "unknown"
        git_commit = "unknown"
        try:
            # Safe read-only subprocesses
            branch_cmd = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, cwd=self.workspace_root, check=True)
            git_branch = branch_cmd.stdout.strip()
            commit_cmd = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=self.workspace_root, check=True)
            git_commit = commit_cmd.stdout.strip()
        except Exception:
            pass

        context = {
            "audit_run_id": audit_run_id,
            "scanner": "collect_system_context",
            "status": "PASSED",
            "findings": [],
            "evidence_refs": [],
            "created_at": datetime.now().isoformat(),
            "workspace_root": self.workspace_root,
            "git": {
                "branch": git_branch,
                "commit": git_commit
            },
            "environment": {
                "os": sys.platform,
                "python_version": sys.version
            }
        }
        save_artifact(audit_run_id, "system_context.json", context, workspace_root=self.workspace_root)
        return context

    def execute_full_audit(self) -> Dict[str, Any]:
        """
        Executes all scanners, aggregates findings, runs classification, and creates reports.
        """
        audit_run_id = self.generate_run_id()
        
        # 1. Collect Context
        self.collect_system_context(audit_run_id)

        # 2. Run Scanners
        api_scanner = APIContractScanner(self.workspace_root)
        api_art = api_scanner.scan(audit_run_id)
        save_artifact(audit_run_id, "api_contract_audit.json", api_art.to_dict(), workspace_root=self.workspace_root)

        dash_scanner = DashboardHealthScanner(self.workspace_root)
        dash_art = dash_scanner.scan(audit_run_id)
        save_artifact(audit_run_id, "dashboard_health_audit.json", dash_art.to_dict(), workspace_root=self.workspace_root)

        ds_scanner = DashboardDataSourceContractScanner(self.workspace_root)
        ds_art = ds_scanner.scan(audit_run_id)
        save_artifact(audit_run_id, "dashboard_data_source_contract_audit.json", ds_art.to_dict(), workspace_root=self.workspace_root)

        tb_scanner = TestBuildScanner(self.workspace_root)
        tb_art = tb_scanner.scan(audit_run_id)
        save_artifact(audit_run_id, "test_build_audit.json", tb_art.to_dict(), workspace_root=self.workspace_root)

        sec_scanner = SecurityGuardrailScanner(self.workspace_root)
        sec_art = sec_scanner.scan(audit_run_id)
        save_artifact(audit_run_id, "security_guardrail_audit.json", sec_art.to_dict(), workspace_root=self.workspace_root)

        pf_scanner = ProjectFactoryReadinessScanner(self.workspace_root)
        pf_art = pf_scanner.scan(audit_run_id)
        save_artifact(audit_run_id, "project_factory_audit.json", pf_art.to_dict(), workspace_root=self.workspace_root)

        # Gather all findings
        all_findings = []
        all_findings.extend(api_art.findings)
        all_findings.extend(dash_art.findings)
        all_findings.extend(ds_art.findings)
        all_findings.extend(tb_art.findings)
        all_findings.extend(sec_art.findings)
        all_findings.extend(pf_art.findings)

        # 3. Classify and Score Findings
        classified = classify_findings(all_findings)
        classified_dicts = [f.to_dict() for f in classified]
        
        classified_art = {
            "audit_run_id": audit_run_id,
            "scanner": "finding_classifier",
            "status": "PASSED" if not classified else "WARNING",
            "findings": classified_dicts,
            "evidence_refs": [],
            "created_at": datetime.now().isoformat()
        }
        save_artifact(audit_run_id, "classified_findings.json", classified_art, workspace_root=self.workspace_root)

        # 4. Generate Final Audit Report
        summary_status = "PASSED"
        if any(art.status == "FAILED" for art in [api_art, dash_art, ds_art, tb_art, sec_art, pf_art]):
            summary_status = "FAILED"
        elif any(art.status == "WARNING" for art in [api_art, dash_art, ds_art, tb_art, sec_art, pf_art]):
            summary_status = "WARNING"

        final_report = {
            "audit_run_id": audit_run_id,
            "scanner": "create_audit_report",
            "status": summary_status,
            "findings": classified_dicts,
            "evidence_refs": [],
            "created_at": datetime.now().isoformat(),
            "summary": {
                "total_findings": len(classified_dicts),
                "categories": {
                    "api_contract": len([f for f in classified if f.category == "api_contract"]),
                    "dashboard_health": len([f for f in classified if f.category == "dashboard_health"]),
                    "test_build": len([f for f in classified if f.category == "test_build"]),
                    "security": len([f for f in classified if f.category == "security"]),
                    "project_factory": len([f for f in classified if f.category == "project_factory"])
                },
                "severities": {
                    "CRITICAL": len([f for f in classified if f.severity == "CRITICAL"]),
                    "HIGH": len([f for f in classified if f.severity == "HIGH"]),
                    "MEDIUM": len([f for f in classified if f.severity == "MEDIUM"]),
                    "LOW": len([f for f in classified if f.severity == "LOW"]),
                    "INFO": len([f for f in classified if f.severity == "INFO"])
                }
            }
        }
        save_artifact(audit_run_id, "audit_report.json", final_report, workspace_root=self.workspace_root)

        return final_report

# Taskflow Step Handler Functions (Sequential API wrappers)
def collect_system_context_step(context: Dict[str, Any]) -> Dict[str, Any]:
    run_id = context.get("audit_run_id") or AuditOrchestrator().generate_run_id()
    orch = AuditOrchestrator(context.get("workspace_root"))
    sys_ctx = orch.collect_system_context(run_id)
    context.update({
        "audit_run_id": run_id,
        "workspace_root": orch.workspace_root,
        "system_context": sys_ctx
    })
    return context

def scan_api_contracts_step(context: Dict[str, Any]) -> Dict[str, Any]:
    orch = AuditOrchestrator(context.get("workspace_root"))
    scanner = APIContractScanner(orch.workspace_root)
    art = scanner.scan(context["audit_run_id"])
    save_artifact(context["audit_run_id"], "api_contract_audit.json", art.to_dict(), workspace_root=orch.workspace_root)
    context.setdefault("findings", []).extend(art.findings)
    context.setdefault("artifacts", {})["api_contract_audit"] = art.to_dict()
    return context

def scan_dashboard_health_step(context: Dict[str, Any]) -> Dict[str, Any]:
    orch = AuditOrchestrator(context.get("workspace_root"))
    scanner = DashboardHealthScanner(orch.workspace_root)
    art = scanner.scan(context["audit_run_id"])
    save_artifact(context["audit_run_id"], "dashboard_health_audit.json", art.to_dict(), workspace_root=orch.workspace_root)
    context.setdefault("findings", []).extend(art.findings)
    context.setdefault("artifacts", {})["dashboard_health_audit"] = art.to_dict()
    return context

def scan_dashboard_data_source_contracts_step(context: Dict[str, Any]) -> Dict[str, Any]:
    orch = AuditOrchestrator(context.get("workspace_root"))
    scanner = DashboardDataSourceContractScanner(orch.workspace_root)
    art = scanner.scan(context["audit_run_id"])
    save_artifact(context["audit_run_id"], "dashboard_data_source_contract_audit.json", art.to_dict(), workspace_root=orch.workspace_root)
    context.setdefault("findings", []).extend(art.findings)
    context.setdefault("artifacts", {})["dashboard_data_source_contract_audit"] = art.to_dict()
    return context

def scan_test_build_step(context: Dict[str, Any]) -> Dict[str, Any]:
    orch = AuditOrchestrator(context.get("workspace_root"))
    scanner = TestBuildScanner(orch.workspace_root)
    art = scanner.scan(context["audit_run_id"])
    save_artifact(context["audit_run_id"], "test_build_audit.json", art.to_dict(), workspace_root=orch.workspace_root)
    context.setdefault("findings", []).extend(art.findings)
    context.setdefault("artifacts", {})["test_build_audit"] = art.to_dict()
    return context

def scan_security_guardrails_step(context: Dict[str, Any]) -> Dict[str, Any]:
    orch = AuditOrchestrator(context.get("workspace_root"))
    scanner = SecurityGuardrailScanner(orch.workspace_root)
    art = scanner.scan(context["audit_run_id"])
    save_artifact(context["audit_run_id"], "security_guardrail_audit.json", art.to_dict(), workspace_root=orch.workspace_root)
    context.setdefault("findings", []).extend(art.findings)
    context.setdefault("artifacts", {})["security_guardrail_audit"] = art.to_dict()
    return context

def scan_project_factory_readiness_step(context: Dict[str, Any]) -> Dict[str, Any]:
    orch = AuditOrchestrator(context.get("workspace_root"))
    scanner = ProjectFactoryReadinessScanner(orch.workspace_root)
    art = scanner.scan(context["audit_run_id"])
    save_artifact(context["audit_run_id"], "project_factory_audit.json", art.to_dict(), workspace_root=orch.workspace_root)
    context.setdefault("findings", []).extend(art.findings)
    context.setdefault("artifacts", {})["project_factory_audit"] = art.to_dict()
    return context

def classify_findings_step(context: Dict[str, Any]) -> Dict[str, Any]:
    orch = AuditOrchestrator(context.get("workspace_root"))
    raw_findings = context.get("findings", [])
    classified = classify_findings(raw_findings)
    classified_dicts = [f.to_dict() for f in classified]
    
    classified_art = {
        "audit_run_id": context["audit_run_id"],
        "scanner": "finding_classifier",
        "status": "PASSED" if not classified else "WARNING",
        "findings": classified_dicts,
        "evidence_refs": [],
        "created_at": datetime.now().isoformat()
    }
    save_artifact(context["audit_run_id"], "classified_findings.json", classified_art, workspace_root=orch.workspace_root)
    context["classified_findings"] = classified_dicts
    return context

def create_audit_report_step(context: Dict[str, Any]) -> Dict[str, Any]:
    run_id = context["audit_run_id"]
    orch = AuditOrchestrator(context.get("workspace_root"))
    classified_dicts = context.get("classified_findings", [])
    
    # Analyze global status
    arts = context.get("artifacts", {}).values()
    summary_status = "PASSED"
    if any(art.get("status") == "FAILED" for art in arts):
        summary_status = "FAILED"
    elif any(art.get("status") == "WARNING" for art in arts):
        summary_status = "WARNING"

    final_report = {
        "audit_run_id": run_id,
        "scanner": "create_audit_report",
        "status": summary_status,
        "findings": classified_dicts,
        "evidence_refs": [],
        "created_at": datetime.now().isoformat(),
        "summary": {
            "total_findings": len(classified_dicts),
            "categories": {
                "api_contract": len([f for f in classified_dicts if f["category"] == "api_contract"]),
                "dashboard_health": len([f for f in classified_dicts if f["category"] == "dashboard_health"]),
                "test_build": len([f for f in classified_dicts if f["category"] == "test_build"]),
                "security": len([f for f in classified_dicts if f["category"] == "security"]),
                "project_factory": len([f for f in classified_dicts if f["category"] == "project_factory"])
            },
            "severities": {
                "CRITICAL": len([f for f in classified_dicts if f["severity"] == "CRITICAL"]),
                "HIGH": len([f for f in classified_dicts if f["severity"] == "HIGH"]),
                "MEDIUM": len([f for f in classified_dicts if f["severity"] == "MEDIUM"]),
                "LOW": len([f for f in classified_dicts if f["severity"] == "LOW"]),
                "INFO": len([f for f in classified_dicts if f["severity"] == "INFO"])
            }
        }
    }
    save_artifact(run_id, "audit_report.json", final_report, workspace_root=orch.workspace_root)
    context["audit_report"] = final_report
    return context
