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
from services.orchestration.economic_engine import economic_engine
from services.orchestration.calibration_engine import calibration_engine

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
        known_regions = mesh_state_store.get_all_regions()
        healthy_count = mesh_state_store.get_healthy_region_count()
        risk_level = str(task.context.get("risk", "")).upper()
        requires_write_quorum = risk_level in {"HIGH", "CRITICAL"}
        if known_regions and requires_write_quorum and not mesh_state_store.is_quorum_maintained():
            # If we lost quorum, we cannot safely commit changes across regions.
            # We raise an exception to trigger 'Advisory Mode' in the calling worker.
            raise QuorumLossException(
                f"Mesh integrity compromised. Quorum lost (Healthy: {healthy_count}). "
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
                    
                    # Phase 24: Real cost calculation via Economic Engine
                    actual_cost = economic_engine.calculate_task_cost(region["id"], project_config["isolation_tier"])
                    
                    candidates.append(MeshTaskRouting(
                        task_id=task.task_id,
                        target_region_id=region["id"],
                        target_cluster_id=cluster_id,
                        latency_ms=current_latency,
                        cost_factor=actual_cost
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

        # 2. Phase 24: Weighted Economic Routing
        # Tier 0 (Critical) -> Weights Latency 90% / Cost 10%
        # Tier 3 (Sandbox) -> Weights Latency 20% / Cost 80%
        
        tier = project_config["isolation_tier"]
        if tier == 0:
            latency_weight, cost_weight = 0.9, 0.1
        elif tier == 3:
            latency_weight, cost_weight = 0.2, 0.8
        else:
            latency_weight, cost_weight = 0.5, 0.5
            
        # Composite score calculation (Lower is better)
        # Note: we use x.latency_ms normalized and inverted (1 - cost_score)
        # For simplicity in this shell, we use a raw weighted sort
        candidates.sort(key=lambda x: (
            (x.latency_ms * latency_weight) + 
            ((1.0 - economic_engine.get_region_cost_score(x.target_region_id)) * 500 * cost_weight)
        ))

        chosen = candidates[0]
        
        # Phase 21: Calibration Link (R-04) - Record Steering Impact
        # We compare chosen cost vs max possible cost in candidates (the 'naive' alternative)
        max_cost = max(c.cost_factor for c in candidates)
        savings = max_cost - chosen.cost_factor
        if savings > 0:
            calibration_engine.record_steering_impact(savings)

        return chosen
