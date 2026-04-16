"""
Sovereign AGI — Phase 20
services/orchestration/mesh_router.py
The Mesh Router - Routes FederationTasks across geographically distributed regions.
"""
from __future__ import annotations
import yaml
import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from services.orchestration.federation_router import FederationTask, FederationRouter
from services.orchestration.latency_adapter import latency_adapter
from services.orchestration.mesh_state_store import mesh_state_store
from services.orchestration.quota_arbitrator import quota_arbitrator, QuotaViolationException, AutonomyViolationException

class MeshTaskRouting(BaseModel):
    task_id: str
    target_region_id: str
    target_cluster_id: str
    latency_ms: float
    cost_factor: float

class QuorumLossException(Exception):
    """Raised when the mesh cannot detect a healthy majority of regions."""
    pass

class MeshRouter:
    def __init__(self, 
                 region_registry_path: str = "configs/region_registry.yaml",
                 cluster_registry_path: str = "configs/agent_cluster_registry.yaml"):
        self.region_registry_path = region_registry_path
        self.cluster_registry_path = cluster_registry_path
        self.regions = self._load_regions()
        self.federation_router = FederationRouter(cluster_registry_path)

    def _load_regions(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.region_registry_path):
            return []
        with open(self.region_registry_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data.get("regions", [])

    async def route_task_to_mesh(self, task: FederationTask) -> Optional[MeshTaskRouting]:
        """
        Determines the best Region + Cluster combination for a task.
        Logic: Quorum Integrity > Region Health > Cluster Expertise > Latency.
        """
        # Phase 21: Quorum Safety Check
        if not mesh_state_store.is_quorum_maintained():
            # If we lost quorum, we cannot safely commit changes across regions.
            # We raise an exception to trigger 'Advisory Mode' in the calling worker.
            raise QuorumLossException(
                f"Mesh integrity compromised. Quorum lost (Healthy: {mesh_state_store.get_healthy_region_count()}). "
                "Switching to Advisory-Only mode."
            )

        # Phase 23: Quota and Autonomy Arbitration
        # In a real environment, we would fetch this config from the Project DB
        # For simulation, we assume reasonable defaults based on task metadata
        project_config = {
            "id": task.project_id,
            "priority": task.priority,
            "isolation_tier": task.context.get("isolation_tier", 2),
            "concurrency_limit": 10,
            "autonomy_envelope": {
                "max_risk_score": 0.5,
                "mode": "autonomous"
            }
        }
        
        # Check if project has quota and if task stays in autonomy envelope
        # This will raise QuotaViolationException or AutonomyViolationException if blocked
        await quota_arbitrator.check_and_reserve(task, project_config)

        candidates: List[MeshTaskRouting] = []
        
        # 1. Identify valid clusters for the task (Expertise Match)
        # We use the existing FederationRouter logic to get candidate cluster types
        
        for region in self.regions:
            if region.get("health_status") != "NOMINAL":
                continue # Skip unhealthy regions

            # Find matching clusters in this specific region
            region_clusters = region.get("active_clusters", [])
            for cluster_id in region_clusters:
                # Validate cluster against task expertise
                specs = self.federation_router.get_cluster_specs(cluster_id)
                if not specs:
                    continue
                
                match_score = len(set(task.required_expertise) & set(specs.get("expertise", [])))
                if match_score > 0:
                    # Evidence-Driven Routing (Phase 20 Stage 3)
                    # We check the Distributed State Store (The Shared Brain) first
                    cached_metrics = mesh_state_store.get_region_metrics(region["id"])
                    if cached_metrics and f"latency_from_us-east-1" in cached_metrics:
                        current_latency = cached_metrics[f"latency_from_us-east-1"]
                        # Periodic recalibration check could go here
                    else:
                        # Fallback to direct probe if state is missing
                        current_latency = await latency_adapter.get_latency(
                            source_region="us-east-1", 
                            target_region=region["id"]
                        )
                    
                    mock_cost = 1.0 + (specs.get("priority", 0) * 0.1)

                    candidates.append(MeshTaskRouting(
                        task_id=task.task_id,
                        target_region_id=region["id"],
                        target_cluster_id=cluster_id,
                        latency_ms=current_latency,
                        cost_factor=mock_cost
                    ))

        if not candidates:
            # Fallback to primary region's default logic cluster
            return MeshTaskRouting(
                task_id=task.task_id,
                target_region_id="us-east-1",
                target_cluster_id="logic-cortex-v1",
                latency_ms=150.0,
                cost_factor=1.0
            )

        # 2. Sort candidates by Latency (Primary) and Cost (Secondary)
        # Phase 23 Expansion: We could also weight by regional project density
        candidates.sort(key=lambda x: (x.latency_ms, x.cost_factor))

        return candidates[0]
