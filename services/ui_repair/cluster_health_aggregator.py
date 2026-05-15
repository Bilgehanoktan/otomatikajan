import logging
from typing import List, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from libs.db.models.ui_repair_models import UIClusterProfile, UIClusterHealthSnapshot

logger = logging.getLogger(__name__)

class ClusterHealthAggregator:
    """
    Aggregates health telemetry from all federated clusters for global monitoring.
    """

    @staticmethod
    async def get_federated_health_summary(db: AsyncSession) -> Dict[str, Any]:
        """Returns a summary of all active clusters and their health scores."""
        # 1. Get all clusters
        clusters_stmt = select(UIClusterProfile)
        clusters = (await db.execute(clusters_stmt)).scalars().all()
        
        total_clusters = len(clusters)
        healthy_count = sum(1 for c in clusters if c.status == "HEALTHY")
        degraded_count = sum(1 for c in clusters if c.status == "DEGRADED")
        offline_count = sum(1 for c in clusters if c.status == "OFFLINE")

        # 2. Get latest snapshots for each
        cluster_details = []
        for cluster in clusters:
            snapshot_stmt = (
                select(UIClusterHealthSnapshot)
                .where(UIClusterHealthSnapshot.cluster_key == cluster.cluster_key)
                .order_by(UIClusterHealthSnapshot.captured_at.desc())
                .limit(1)
            )
            snapshot = (await db.execute(snapshot_stmt)).scalar_one_or_none()
            
            cluster_details.append({
                "cluster_key": cluster.cluster_key,
                "cluster_name": cluster.cluster_name,
                "region": cluster.region,
                "environment": cluster.environment,
                "status": cluster.status,
                "health_score": snapshot.health_score if snapshot else 0.0,
                "active_repairs": snapshot.active_repairs if snapshot else 0,
                "latency_ms": snapshot.latency_ms if snapshot else 0,
                "last_sync": snapshot.captured_at.isoformat() if snapshot else None
            })

        return {
            "summary": {
                "total": total_clusters,
                "healthy": healthy_count,
                "degraded": degraded_count,
                "offline": offline_count,
                "global_health_score": (healthy_count / total_clusters * 100) if total_clusters > 0 else 0
            },
            "clusters": cluster_details
        }
