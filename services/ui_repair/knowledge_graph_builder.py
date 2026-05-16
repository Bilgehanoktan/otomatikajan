from typing import List, Dict, Any
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from libs.db.models.ui_repair_models import (
    UIKnowledgeNode, UIKnowledgeEdge,
    UIIncidentWarRoom, UIComplianceFinding,
    UISecurityRemediationPlan, UIAutoPatchExecution,
    UIPatchCandidate, UIPolicyEvaluation,
    UISovereignIdentity, UIToolCallAudit,
    UIRedTeamFinding, UISLOBreach, UICostAnomaly
)
from services.ui_repair.graph_node_extractor import GraphNodeExtractor
from services.ui_repair.graph_edge_inferencer import GraphEdgeInferencer

logger = logging.getLogger(__name__)

class KnowledgeGraphBuilder:
    """Orchestrates the building and maintenance of the Knowledge Graph."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def rebuild_graph(self) -> Dict[str, int]:
        """Clears and rebuilds the entire knowledge graph from current data."""
        logger.info("Rebuilding Knowledge Graph...")
        
        # 1. Clear existing graph
        await self.db.execute(delete(UIKnowledgeEdge))
        await self.db.execute(delete(UIKnowledgeNode))
        await self.db.commit()
        
        counts = {
            "nodes": 0,
            "edges": 0
        }
        
        # 2. Extract Nodes from all relevant entities
        entities = [
            (UIIncidentWarRoom, GraphNodeExtractor.from_incident_war_room),
            (UIComplianceFinding, GraphNodeExtractor.from_security_finding),
            (UISecurityRemediationPlan, GraphNodeExtractor.from_remediation_plan),
            (UIAutoPatchExecution, GraphNodeExtractor.from_autopatch_execution),
            (UIPatchCandidate, GraphNodeExtractor.from_patch_candidate),
            (UIPolicyEvaluation, GraphNodeExtractor.from_policy_decision),
            (UISovereignIdentity, GraphNodeExtractor.from_identity),
            (UIToolCallAudit, GraphNodeExtractor.from_tool_audit),
            (UIRedTeamFinding, GraphNodeExtractor.from_red_team_finding),
            (UISLOBreach, GraphNodeExtractor.from_slo_breach),
            (UICostAnomaly, GraphNodeExtractor.from_cost_anomaly)
        ]
        
        for model, extractor in entities:
            stmt = select(model)
            result = await self.db.execute(stmt)
            objects = result.scalars().all()
            
            for obj in objects:
                try:
                    node = extractor(obj)
                    self.db.add(node)
                    counts["nodes"] += 1
                    
                    # Infer edges for this node/object
                    edges = GraphEdgeInferencer.infer_edges(node, obj)
                    for edge in edges:
                        self.db.add(edge)
                        counts["edges"] += 1
                except Exception as e:
                    logger.error(f"Failed to extract node/edges for {model.__name__} {getattr(obj, 'id', 'unknown')}: {e}")

        await self.db.commit()
        logger.info(f"Knowledge Graph rebuilt: {counts['nodes']} nodes, {counts['edges']} edges.")
        return counts

    async def get_graph_overview(self) -> Dict[str, Any]:
        """Returns summary statistics for the knowledge graph."""
        node_count_stmt = select(UIKnowledgeNode.node_type).select_from(UIKnowledgeNode)
        res_nodes = await self.db.execute(node_count_stmt)
        node_types = res_nodes.scalars().all()
        
        edge_count_stmt = select(UIKnowledgeEdge.edge_type).select_from(UIKnowledgeEdge)
        res_edges = await self.db.execute(edge_count_stmt)
        edge_types = res_edges.scalars().all()
        
        node_stats = {}
        for nt in node_types:
            node_stats[nt] = node_stats.get(nt, 0) + 1
            
        edge_stats = {}
        for et in edge_types:
            edge_stats[et] = edge_stats.get(et, 0) + 1
            
        return {
            "total_nodes": len(node_types),
            "total_edges": len(edge_types),
            "node_type_counts": node_stats,
            "edge_type_counts": edge_stats,
            "last_rebuild_at": None # Could be tracked in a separate metadata table
        }
