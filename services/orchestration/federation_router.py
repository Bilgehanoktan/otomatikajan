"""
Sovereign AGI — Phase 19
services/orchestration/federation_router.py
The Federation Router - Dispatches goals to specialized agent clusters.
"""
from __future__ import annotations
import yaml
import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class FederationTask(BaseModel):
    task_id: str
    project_id: str                   # Phase 23: Track project ownership
    goal_description: str
    required_expertise: List[str]
    context: Dict[str, Any]
    priority: str = "medium"          # Phase 23: Fleet priority (critical/high/medium/low)
    priority_override: Optional[int] = None

class FederationRouter:
    def __init__(self, registry_path: str = "configs/agent_cluster_registry.yaml"):
        self.registry_path = registry_path
        self.clusters = self._load_registry()

    def _load_registry(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.registry_path):
            return []
        with open(self.registry_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data.get("clusters", [])

    async def route_task(self, task: FederationTask) -> Optional[str]:
        """
        Matches a task to the best specialized cluster based on expertise and priority.
        Returns the cluster_id.
        """
        candidates = []
        for cluster in self.clusters:
            # Simple intersection check for expertise
            match_score = len(set(task.required_expertise) & set(cluster.get("expertise", [])))
            if match_score > 0:
                candidates.append({
                    "cluster_id": cluster["id"],
                    "match_score": match_score,
                    "priority": cluster.get("priority", 0)
                })
        
        if not candidates:
            return "logic-cortex-v1" # Default fallback
            
        # Sort by match_score (primary) and priority (secondary)
        candidates.sort(key=lambda x: (x["match_score"], x["priority"]), reverse=True)
        
        return candidates[0]["cluster_id"]

    def get_cluster_specs(self, cluster_id: str) -> Optional[Dict[str, Any]]:
        for cluster in self.clusters:
            if cluster["id"] == cluster_id:
                return cluster
        return None
