import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from libs.db.models.ui_repair_models import (
    UIKnowledgeNode, KnowledgeNodeType,
    UIIncidentWarRoom, UIComplianceFinding,
    UISecurityRemediationPlan, UIAutoPatchExecution,
    UIPatchCandidate, UIRepairCase, UIRepairAttempt,
    UIPolicyEvaluation, UIPolicyDrift, UISovereignIdentity,
    UIToolCallAudit, UIResiliencyMeshNode, UIClusterFailoverEvent,
    UIRedTeamFinding, UIAttackPath, UICognitiveIntegrityCheck,
    UISLOBreach, UICostEvent
)

class GraphNodeExtractor:
    """Extracts UIKnowledgeNodes from existing database models."""

    @staticmethod
    def from_incident_war_room(war_room: UIIncidentWarRoom) -> UIKnowledgeNode:
        return UIKnowledgeNode(
            node_key=f"WAR_ROOM:{war_room.id}",
            node_type=KnowledgeNodeType.WAR_ROOM,
            source_type="WAR_ROOM",
            source_id=str(war_room.id),
            tenant_key=war_room.tenant_key,
            project_key=war_room.project_key,
            cluster_key=war_room.cluster_key,
            title=war_room.title or f"War Room {war_room.incident_key}",
            summary=f"War room for incident {war_room.incident_key}. Status: {war_room.status}",
            severity=str(war_room.severity),
            metadata_json={
                "status": str(war_room.status),
                "incident_key": war_room.incident_key,
                "commander": war_room.assigned_commander
            }
        )

    @staticmethod
    def from_security_finding(finding: UIComplianceFinding) -> UIKnowledgeNode:
        return UIKnowledgeNode(
            node_key=f"SECURITY_FINDING:{finding.id}",
            node_type=KnowledgeNodeType.SECURITY_FINDING,
            source_type="SECURITY_FINDING",
            source_id=str(finding.id),
            tenant_key=finding.tenant_key,
            project_key=finding.project_key,
            cluster_key=finding.cluster_key,
            title=finding.description[:100] if finding.description else f"Finding {finding.id}",
            summary=finding.description,
            severity=finding.severity,
            metadata_json={
                "finding_type": finding.finding_type,
                "standard": finding.standard,
                "status": finding.status
            }
        )

    @staticmethod
    def from_remediation_plan(plan: UISecurityRemediationPlan) -> UIKnowledgeNode:
        return UIKnowledgeNode(
            node_key=f"REMEDIATION_PLAN:{plan.id}",
            node_type=KnowledgeNodeType.REMEDIATION_PLAN,
            source_type="REMEDIATION_PLAN",
            source_id=str(plan.id),
            tenant_key=plan.tenant_key,
            project_key=plan.project_key,
            title=plan.title,
            summary=plan.description,
            severity="INFO",
            metadata_json={
                "finding_id": str(plan.finding_id),
                "strategy": plan.remediation_strategy,
                "status": plan.status
            }
        )

    @staticmethod
    def from_autopatch_execution(execution: UIAutoPatchExecution) -> UIKnowledgeNode:
        return UIKnowledgeNode(
            node_key=f"AUTOPATCH_EXECUTION:{execution.id}",
            node_type=KnowledgeNodeType.AUTOPATCH_EXECUTION,
            source_type="AUTOPATCH_EXECUTION",
            source_id=str(execution.id),
            project_key=execution.project_key,
            title=f"Auto-Patch for {execution.affected_route}",
            summary=f"Execution of patch for {execution.affected_route}. Status: {execution.status}",
            severity="INFO",
            metadata_json={
                "case_id": str(execution.case_id),
                "route": execution.affected_route,
                "status": execution.status
            }
        )

    @staticmethod
    def from_patch_candidate(candidate: UIPatchCandidate) -> UIKnowledgeNode:
        return UIKnowledgeNode(
            node_key=f"PATCH_CANDIDATE:{candidate.id}",
            node_type=KnowledgeNodeType.PATCH_CANDIDATE,
            source_type="PATCH_CANDIDATE",
            source_id=str(candidate.id),
            title=f"Patch Candidate {candidate.id}",
            summary=candidate.patch_summary,
            severity="INFO",
            metadata_json={
                "execution_id": str(candidate.execution_id),
                "strategy": candidate.strategy_name,
                "confidence": candidate.confidence_score
            }
        )

    @staticmethod
    def from_policy_decision(eval: UIPolicyEvaluation) -> UIKnowledgeNode:
        return UIKnowledgeNode(
            node_key=f"POLICY_DECISION:{eval.id}",
            node_type=KnowledgeNodeType.POLICY_DECISION,
            source_type="POLICY_EVALUATION",
            source_id=str(eval.id),
            tenant_key=eval.tenant_key,
            project_key=eval.project_key,
            title=f"Policy Decision: {eval.policy_key}",
            summary=f"Decision {eval.decision} for {eval.policy_key}",
            severity="INFO" if eval.decision == "ALLOW" else "MEDIUM",
            metadata_json={
                "policy_key": eval.policy_key,
                "decision": eval.decision,
                "reason": eval.reason
            }
        )

    @staticmethod
    def from_identity(identity: UISovereignIdentity) -> UIKnowledgeNode:
        return UIKnowledgeNode(
            node_key=f"IDENTITY:{identity.id}",
            node_type=KnowledgeNodeType.IDENTITY,
            source_type="IDENTITY",
            source_id=str(identity.id),
            tenant_key=identity.tenant_key,
            title=f"Identity: {identity.identity_name}",
            summary=f"Identity {identity.identity_key} for {identity.owner_type}",
            severity="INFO",
            metadata_json={
                "identity_key": identity.identity_key,
                "owner_type": identity.owner_type,
                "trust_score": identity.trust_score
            }
        )

    @staticmethod
    def from_tool_audit(audit: UIToolCallAudit) -> UIKnowledgeNode:
        return UIKnowledgeNode(
            node_key=f"TOOL_CALL:{audit.id}",
            node_type=KnowledgeNodeType.TOOL_CALL,
            source_type="TOOL_CALL",
            source_id=str(audit.id),
            tenant_key=audit.tenant_key,
            project_key=audit.project_key,
            title=f"Tool Call: {audit.tool_name}",
            summary=f"Execution of tool {audit.tool_name} by {audit.agent_id}",
            severity="INFO" if audit.governance_status == "APPROVED" else "HIGH",
            metadata_json={
                "tool_name": audit.tool_name,
                "agent_id": audit.agent_id,
                "governance_status": audit.governance_status
            }
        )

    @staticmethod
    def from_red_team_finding(finding: UIRedTeamFinding) -> UIKnowledgeNode:
        return UIKnowledgeNode(
            node_key=f"RED_TEAM_FINDING:{finding.id}",
            node_type=KnowledgeNodeType.RED_TEAM_FINDING,
            source_type="RED_TEAM_FINDING",
            source_id=str(finding.id),
            title=finding.title,
            summary=finding.description,
            severity=finding.severity,
            metadata_json={
                "run_id": str(finding.run_id),
                "attack_type": finding.attack_type,
                "exploitability": finding.exploitability
            }
        )

    @staticmethod
    def from_slo_breach(breach: UISLOBreach) -> UIKnowledgeNode:
        return UIKnowledgeNode(
            node_key=f"SLO_BREACH:{breach.id}",
            node_type=KnowledgeNodeType.SLO_BREACH,
            source_type="SLO_BREACH",
            source_id=str(breach.id),
            project_key=breach.project_key,
            title=f"SLO Breach: {breach.slo_name}",
            summary=f"SLO {breach.slo_name} breached with value {breach.observed_value} (Target: {breach.target_value})",
            severity=breach.severity,
            metadata_json={
                "slo_name": breach.slo_name,
                "observed_value": breach.observed_value,
                "target_value": breach.target_value
            }
        )

    @staticmethod
    def from_cost_anomaly(anomaly: Any) -> UIKnowledgeNode:
        # Assuming UICostAnomaly exists or we handle it generically
        return UIKnowledgeNode(
            node_key=f"COST_ANOMALY:{anomaly.id}",
            node_type=KnowledgeNodeType.COST_ANOMALY,
            source_type="COST_ANOMALY",
            source_id=str(anomaly.id),
            project_key=anomaly.project_key,
            title=f"Cost Anomaly: {anomaly.anomaly_type}",
            summary=anomaly.reason,
            severity=anomaly.severity,
            metadata_json={
                "anomaly_type": anomaly.anomaly_type,
                "observed": anomaly.observed_cost_usd,
                "expected": anomaly.expected_cost_usd
            }
        )
