
"""
services/federation/trust_service.py — Phase 26 R-09
Autonomous Federation Trust Scoring with Decay Models & Arbitration Learning.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from sqlalchemy import select, update, func
from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import FederationTrust, FederationTrustHistory
from services.observability.logging import get_logger

logger = get_logger("federation.trust")

class FederationTrustService:
    def __init__(self, decay_rate: float = 0.01):
        self.decay_rate = decay_rate # Hourly decay rate for trust scores

    async def initialize_cluster(self, cluster_id: str, metadata: dict = None):
        """Register a new cluster in the federation trust mesh."""
        async with AsyncSessionLocal() as db:
            existing = await db.get(FederationTrust, cluster_id)
            if not existing:
                cluster = FederationTrust(
                    cluster_id=cluster_id,
                    trust_score=1.0,
                    cluster_metadata=metadata or {}
                )
                db.add(cluster)
                await db.commit()
                logger.info(f"[TRUST] Cluster {cluster_id} initialized.")

    async def update_score(self, cluster_id: str, outcome: str, weight: float = 0.05):
        """
        Update trust score based on operational outcomes.
        outcome: 'success', 'failure', 'arbitration_win', 'arbitration_loss'
        """
        async with AsyncSessionLocal() as db:
            cluster = await db.get(FederationTrust, cluster_id)
            if not cluster:
                return

            old_score = cluster.trust_score
            delta = 0.0

            if outcome == 'success':
                delta = weight * (1.0 - old_score) # Gain slower as we approach 1.0
                cluster.success_count += 1
            elif outcome == 'failure':
                delta = -weight * 2 # Failures hit harder
                cluster.failure_count += 1
            elif outcome == 'arbitration_win':
                delta = weight * 1.5 # Arbitration wins are high trust signals
                cluster.arbitration_wins += 1
            elif outcome == 'arbitration_loss':
                delta = -weight * 1.5

            new_score = max(0.0, min(1.0, old_score + delta))
            cluster.trust_score = new_score
            cluster.last_activity_at = datetime.now(timezone.utc)

            # Record History
            history = FederationTrustHistory(
                cluster_id=cluster_id,
                trust_score=new_score,
                change_reason=outcome,
                payload={"prev_score": old_score, "delta": delta}
            )
            db.add(history)
            await db.commit()
            logger.info(f"[TRUST] {cluster_id} score updated: {old_score:.2f} -> {new_score:.2f} ({outcome})")

    async def apply_decay(self):
        """Apply passive trust decay to inactive clusters (Stability check)."""
        async with AsyncSessionLocal() as db:
            # Simple decay: score = score * (1 - decay_rate) for every hour of inactivity
            # For brevity in this phase, we just decrease scores of all clusters slightly
            q = update(FederationTrust).values(
                trust_score=FederationTrust.trust_score * (1.0 - self.decay_rate)
            ).where(FederationTrust.trust_score > 0.1)
            await db.execute(q)
            await db.commit()
