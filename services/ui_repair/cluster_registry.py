import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from libs.db.models.ui_repair_models import (
    UIClusterProfile, UIClusterHealthSnapshot
)
from services.ui_repair.schemas import (
    UIClusterProfileCreate, UIClusterHealthSnapshotCreate
)

logger = logging.getLogger(__name__)

class ClusterRegistry:
    """
    Manages regional and environmental cluster profiles and health telemetry.
    """

    @staticmethod
    async def create_cluster(db: AsyncSession, data: UIClusterProfileCreate) -> UIClusterProfile:
        """Registers a new regional or environmental cluster."""
        cluster = UIClusterProfile(
            cluster_key=data.cluster_key,
            cluster_name=data.cluster_name,
            region=data.region or "global",
            environment=data.environment or "production",
            provider=data.provider or "Sovereign",
            status="HEALTHY",
            cluster_metadata=data.cluster_metadata or {}
        )
        db.add(cluster)
        await db.commit()
        await db.refresh(cluster)
        logger.info(f"Cluster created: {cluster.cluster_key}")
        return cluster

    @staticmethod
    async def list_clusters(db: AsyncSession) -> List[UIClusterProfile]:
        """Lists all registered clusters."""
        stmt = select(UIClusterProfile)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_cluster(db: AsyncSession, cluster_key: str) -> Optional[UIClusterProfile]:
        """Retrieves a cluster profile by its unique key."""
        stmt = select(UIClusterProfile).where(UIClusterProfile.cluster_key == cluster_key)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def record_health_snapshot(db: AsyncSession, data: UIClusterHealthSnapshotCreate) -> UIClusterHealthSnapshot:
        """Records a new health telemetry snapshot for a cluster."""
        snapshot = UIClusterHealthSnapshot(
            cluster_key=data.cluster_key,
            health_score=data.health_score,
            active_repairs=data.active_repairs,
            failed_repairs_24h=data.failed_repairs_24h,
            latency_ms=data.latency_ms,
            status_brief=data.status_brief,
            metrics_json=data.metrics_json or {}
        )
        db.add(snapshot)
        
        # Update cluster status if health score is low
        if data.health_score < 50:
            status = "DEGRADED"
        elif data.health_score < 10:
            status = "OFFLINE"
        else:
            status = "HEALTHY"
            
        await db.execute(
            update(UIClusterProfile)
            .where(UIClusterProfile.cluster_key == data.cluster_key)
            .values(status=status)
        )
        
        await db.commit()
        await db.refresh(snapshot)
        logger.info(f"Health snapshot recorded for cluster {data.cluster_key}: {status}")
        return snapshot

    @staticmethod
    async def get_latest_health(db: AsyncSession, cluster_key: str) -> Optional[UIClusterHealthSnapshot]:
        """Retrieves the most recent health snapshot for a cluster."""
        stmt = (
            select(UIClusterHealthSnapshot)
            .where(UIClusterHealthSnapshot.cluster_key == cluster_key)
            .order_by(UIClusterHealthSnapshot.captured_at.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
