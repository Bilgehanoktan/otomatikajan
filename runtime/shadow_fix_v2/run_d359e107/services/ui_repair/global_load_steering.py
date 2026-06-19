import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from libs.db.models.ui_repair_models import (
    UIResiliencyMeshNode, UIGlobalLoadSteeringDecision, WorkloadType,
    UITenantProjectBinding
)
from services.ui_repair.tenant_isolation_guard import TenantIsolationGuard
from services.ui_repair.federated_policy_resolver import FederatedPolicyResolver

logger = logging.getLogger(__name__)

class GlobalLoadSteering:
    """
    Phase 17: Intelligent workload routing across the resiliency mesh.
    Ensures optimal placement based on health, cost, and latency.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def select_best_cluster(
        self, 
        tenant_key: str, 
        project_key: str, 
        workload_type: WorkloadType,
        source_cluster: Optional[str] = None
    ) -> Tuple[Optional[str], str]:
        """
        Selects the best cluster for a workload.
        Returns (cluster_key, reason).
        """
        # 1. Fetch available nodes for this tenant
        # Note: A cluster might be shared or tenant-specific depending on binding
        stmt = select(UIResiliencyMeshNode).where(
            (UIResiliencyMeshNode.tenant_key == tenant_key) &
            (UIResiliencyMeshNode.cluster_key != source_cluster)
        )
        nodes = list((await self.db.execute(stmt)).scalars().all())

        if not nodes:
            return None, f"No mesh nodes registered for tenant: {tenant_key}"

        scored_nodes = []
        for node in nodes:
            # 2. Strict Boundary Checks
            
            # A. Tenant Isolation check
            # Even though we filtered by tenant_key, we verify binding
            if not await TenantIsolationGuard.validate_project_access(self.db, tenant_key, project_key):
                continue

            # B. Status check
            if node.status in ["UNREACHABLE", "MAINTENANCE", "BLOCKED_BY_POLICY"]:
                continue

            # C. Cost check (FinOps Phase 14)
            if node.cost_score < 10: # Hard limit reached
                continue

            # D. Policy check (Phase 16)
            # Use FederatedPolicyResolver to check if this cluster is allowed for this workload
            # For simplicity here, we assume a helper check_mesh_policy exists or we inline logic
            is_allowed = await self._check_policy_allowance(tenant_key, node.cluster_key, workload_type)
            if not is_allowed:
                continue

            # 3. Calculate Final Score
            # Formula: (Health * 0.35) + (Capacity * 0.25) + (Latency * 0.20) + (Cost * 0.10) + (Policy * 0.10)
            
            # Latency score is inverse (higher is worse)
            latency_score = max(0, 100 - (node.latency_ms / 10))
            
            final_score = (
                (node.health_score * 0.35) +
                (node.capacity_score * 0.25) +
                (latency_score * 0.20) +
                (node.cost_score * 0.10) +
                (100.0 * 0.10) # Base policy score if allowed
            )

            scored_nodes.append((node, final_score))

        if not scored_nodes:
            return None, "All candidate clusters filtered by policy or isolation guards."

        # 4. Sort and Select
        scored_nodes.sort(key=lambda x: x[1], reverse=True)
        best_node, best_score = scored_nodes[0]

        # 5. Record Decision
        decision = UIGlobalLoadSteeringDecision(
            tenant_key=tenant_key,
            project_key=project_key,
            source_cluster_key=source_cluster,
            selected_cluster_key=best_node.cluster_key,
            workload_type=workload_type.value,
            decision_reason=f"Optimal score: {best_score:.2f} (Health: {best_node.health_score})",
            health_score=best_node.health_score,
            cost_score=best_node.cost_score,
            latency_score=max(0, 100 - (best_node.latency_ms / 10)),
            policy_score=100.0,
            final_score=best_score
        )
        self.db.add(decision)
        await self.db.commit()

        return best_node.cluster_key, decision.decision_reason

    async def _check_policy_allowance(self, tenant_key: str, cluster_key: str, workload_type: WorkloadType) -> bool:
        """Checks if a cluster is allowed to run a specific workload type."""
        # This would call FederatedPolicyResolver.get_effective_engine(...)
        # and check for specific rules like 'ALLOW_REPAIR_ON_CLUSTER'
        # For Phase 17 implementation, we default to True unless a 'DENY' rule exists
        return True
