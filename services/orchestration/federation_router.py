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
from services.orchestration.trust_governor import trust_governor

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
        Matches a task to the best specialized cluster based on expertise, priority, and TRUST SCORE.
        Returns the cluster_id.
        """
        # Load real-time trust scores
        trust_map = await trust_governor.get_trust_map()
        
        candidates = []
        for cluster in self.clusters:
            # Simple intersection check for expertise
            match_score = len(set(task.required_expertise) & set(cluster.get("expertise", [])))
            if match_score > 0:
                cluster_id = cluster["id"]
                trust_score = trust_map.get(cluster_id, 0.8) # Default 0.8 if no history
                
                candidates.append({
                    "cluster_id": cluster_id,
                    "match_score": match_score,
                    "trust_score": trust_score,
                    "priority": cluster.get("priority", 0)
                })
        
        if not candidates:
            return "logic-cortex-v1" # Default fallback
            
        # Sort by match_score (primary), trust_score (secondary), and priority (tertiary)
        candidates.sort(key=lambda x: (x["match_score"], x["trust_score"], x["priority"]), reverse=True)
        
        final_choice = candidates[0]
        # Decay logic check: Trigger decay analysis for the chosen cluster (maintenance pulse)
        # In production this might be a cron, here we do it ad-hoc for simplicity in Faz 26
        await trust_governor.apply_decay(final_choice["cluster_id"])
        
        return final_choice["cluster_id"]

    def get_cluster_specs(self, cluster_id: str) -> Optional[Dict[str, Any]]:
        for cluster in self.clusters:
            if cluster["id"] == cluster_id:
                return cluster
        return None
