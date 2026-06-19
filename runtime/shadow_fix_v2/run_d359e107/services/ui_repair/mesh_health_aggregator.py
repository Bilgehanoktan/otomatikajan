import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from libs.db.models.ui_repair_models import (
    UIResiliencyMeshNode, UIClusterHealthSnapshot, UIRepairCase, 
    UIRepairAttempt, MeshNodeStatus, UIFederatedEvidenceRecord
)
from services.ui_repair.schemas import UIResiliencyMeshNodeCreate

logger = logging.getLogger(__name__)

class MeshHealthAggregator:
    """
    Phase 17: Aggregates real-time health and capacity metrics across the resiliency mesh.
    """

    @staticmethod
    async def register_node(db: AsyncSession, data: UIResiliencyMeshNodeCreate) -> UIResiliencyMeshNode:
        """Registers or updates a mesh node."""
        stmt = select(UIResiliencyMeshNode).where(UIResiliencyMeshNode.cluster_key == data.cluster_key)
        node = (await db.execute(stmt)).scalar_one_or_none()

        if not node:
            node = UIResiliencyMeshNode(
                tenant_key=data.tenant_key,
                cluster_key=data.cluster_key,
                region=data.region,
                environment=data.environment,
                status=data.status.value
            )
            db.add(node)
        else:
            node.status = data.status.value
            node.last_heartbeat_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(node)
        return node

    @staticmethod
    async def process_heartbeat(db: AsyncSession, cluster_key: str, metrics: Dict[str, Any]):
        """Updates node metrics based on a heartbeat."""
        stmt = select(UIResiliencyMeshNode).where(UIResiliencyMeshNode.cluster_key == cluster_key)
        node = (await db.execute(stmt)).scalar_one_or_none()

        if node:
            node.last_heartbeat_at = datetime.now(timezone.utc)
            node.latency_ms = metrics.get("latency_ms", node.latency_ms)
            node.active_repairs = metrics.get("active_repairs", node.active_repairs)
            node.queue_depth = metrics.get("queue_depth", node.queue_depth)
            
            # Recalculate scores
            node.health_score = await MeshHealthAggregator._calculate_health_score(db, cluster_key, metrics)
            node.capacity_score = MeshHealthAggregator._calculate_capacity_score(metrics)
            node.cost_score = metrics.get("cost_score", 100.0)
            
            # Update status based on score
            if node.health_score < 50:
                node.status = MeshNodeStatus.DEGRADED.value
            elif node.queue_depth > 50:
                node.status = MeshNodeStatus.SATURATED.value
            else:
                node.status = MeshNodeStatus.HEALTHY.value

            await db.commit()

    @staticmethod
    async def _calculate_health_score(db: AsyncSession, cluster_key: str, metrics: Dict[str, Any]) -> float:
        """
        Score = f(RouteHealth, MonitoringSuccess, EvidenceSync, Latency)
        """
        # Base from metrics
        score = metrics.get("base_health", 100.0)

        # Penalty for high latency
        latency = metrics.get("latency_ms", 0)
        if latency > 500:
            score -= (latency - 500) / 10

        # Penalty for failed evidence syncs (Phase 16 link)
        sync_stmt = select(func.count(UIFederatedEvidenceRecord.id)).where(
            (UIFederatedEvidenceRecord.cluster_key == cluster_key) &
            (UIFederatedEvidenceRecord.sync_status == "FAILED")
        )
        failed_syncs = (await db.execute(sync_stmt)).scalar() or 0
        score -= min(failed_syncs * 5, 30)

        return max(0.0, min(100.0, score))

    @staticmethod
    def _calculate_capacity_score(metrics: Dict[str, Any]) -> float:
        """Score based on queue depth and active repairs."""
        active = metrics.get("active_repairs", 0)
        queue = metrics.get("queue_depth", 0)
        
        # Assume max capacity per node is 20 active, 100 queue
        capacity = 100.0 - (active * 2.5) - (queue * 0.5)
        return max(0.0, capacity)

    @staticmethod
    async def get_mesh_status(db: AsyncSession) -> Dict[str, Any]:
        """Aggregates status of all nodes."""
        stmt = select(UIResiliencyMeshNode)
        result = await db.execute(stmt)
        nodes = list(result.scalars().all())

        healthy_count = sum(1 for n in nodes if n.status == "HEALTHY")
        
        # Calculate global federation health index
        global_index = 0.0
        if nodes:
            global_index = sum(n.health_score for n in nodes) / len(nodes)

        return {
            "global_federation_health_index": global_index,
            "total_nodes": len(nodes),
            "healthy_nodes": healthy_count,
            "degraded_nodes": len(nodes) - healthy_count,
            "nodes": nodes
        }
