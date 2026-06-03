import uuid
from typing import List, Optional
from libs.db.models.ui_repair_models import (
    UIKnowledgeEdge, KnowledgeEdgeType, UIKnowledgeNode,
    UIIncidentWarRoom, UIComplianceFinding,
    UISecurityRemediationPlan, UIAutoPatchExecution,
    UIPatchCandidate, UIPolicyEvaluation,
    UIToolCallAudit, UIRedTeamFinding, UISLOBreach
)

class GraphEdgeInferencer:
    """Infers relationships (edges) between knowledge nodes."""

    @staticmethod
    def infer_edges(node: UIKnowledgeNode, source_obj: any) -> List[UIKnowledgeEdge]:
        """Infers edges based on foreign keys and logic of the source object."""
        edges = []
        
        if isinstance(source_obj, UIIncidentWarRoom):
            # War Room -> Incident (if we had an incident node)
            if source_obj.incident_id:
                edges.append(UIKnowledgeEdge(
                    source_node_key=f"WAR_ROOM:{source_obj.id}",
                    target_node_key=f"INCIDENT:{source_obj.incident_id}",
                    edge_type=KnowledgeEdgeType.CAUSED_BY # Or TRIGGERED_BY
                ))

        elif isinstance(source_obj, UISecurityRemediationPlan):
            # Plan -> Finding
            if source_obj.finding_id:
                edges.append(UIKnowledgeEdge(
                    source_node_key=f"REMEDIATION_PLAN:{source_obj.id}",
                    target_node_key=f"SECURITY_FINDING:{source_obj.finding_id}",
                    edge_type=KnowledgeEdgeType.MITIGATED_BY
                ))

        elif isinstance(source_obj, UIAutoPatchExecution):
            # Execution -> Case
            if source_obj.case_id:
                edges.append(UIKnowledgeEdge(
                    source_node_key=f"AUTOPATCH_EXECUTION:{source_obj.id}",
                    target_node_key=f"REPAIR_CASE:{source_obj.case_id}",
                    edge_type=KnowledgeEdgeType.TRIGGERED
                ))
            # Execution -> Remediation Plan (if exists)
            # This might require metadata or a direct FK we added in v2

        elif isinstance(source_obj, UIPatchCandidate):
            # Candidate -> Execution
            if source_obj.execution_id:
                edges.append(UIKnowledgeEdge(
                    source_node_key=f"PATCH_CANDIDATE:{source_obj.id}",
                    target_node_key=f"AUTOPATCH_EXECUTION:{source_obj.execution_id}",
                    edge_type=KnowledgeEdgeType.DEPENDS_ON
                ))

        elif isinstance(source_obj, UIPolicyEvaluation):
            # Evaluation -> Identity (if identity node exists)
            # Evaluation -> Tool (if tool node exists)
            pass

        elif isinstance(source_obj, UIToolCallAudit):
            # Tool -> Identity
            if source_obj.caller_id:
                edges.append(UIKnowledgeEdge(
                    source_node_key=f"TOOL_CALL:{source_obj.id}",
                    target_node_key=f"IDENTITY:{source_obj.caller_id}",
                    edge_type=KnowledgeEdgeType.USED_TOOL
                ))

        elif isinstance(source_obj, UIRedTeamFinding):
            # Finding -> Red Team Run
            if source_obj.run_id:
                edges.append(UIKnowledgeEdge(
                    source_node_key=f"RED_TEAM_FINDING:{source_obj.id}",
                    target_node_key=f"RED_TEAM_RUN:{source_obj.run_id}",
                    edge_type=KnowledgeEdgeType.CAUSED_BY
                ))

        elif isinstance(source_obj, UISLOBreach):
            # Breach -> Project (if project node exists)
            pass

        return edges
