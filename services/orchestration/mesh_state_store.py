"""
Sovereign AGI — Phase 20
services/orchestration/mesh_state_store.py
A persistent state store for mesh-wide metrics (Health, Latency).
Uses Redis as the distributed KV store.
"""
from __future__ import annotations
import json
import os
import redis
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class MeshStateStore:
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://redis:6379/0")
        try:
            self._redis = redis.from_url(self.redis_url, decode_responses=True)
            self._key = "sovereign:mesh:state"
            logger.info(f"MeshStateStore initialized with Redis: {self.redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis for MeshStateStore: {e}")
            self._redis = None

    def _get_state(self) -> Dict[str, Any]:
        if not self._redis:
            return {"regions": {}, "last_update": None}
        try:
            data = self._redis.get(self._key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.error(f"Error reading mesh state from Redis: {e}")
        return {"regions": {}, "last_update": None}

    def _save_state(self, state: Dict[str, Any]):
        if not self._redis:
            return
        try:
            state["last_update"] = datetime.now(timezone.utc).isoformat()
            self._redis.set(self._key, json.dumps(state))
        except Exception as e:
            logger.error(f"Error saving mesh state to Redis: {e}")

    def update_region(self, region_id: str, metrics: Dict[str, Any]):
        self.set_region_metrics(region_id, metrics)

    def set_region_metrics(self, region_id: str, metrics: Dict[str, Any]):
        state = self._get_state()
        if "regions" not in state:
            state["regions"] = {}
        
        current = state["regions"].get(region_id, {})
        current.update(metrics)
        current["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        state["regions"][region_id] = current
        self._save_state(state)

    def get_region_status(self, region_id: str) -> Optional[Dict[str, Any]]:
        return self.get_region_metrics(region_id)

    def get_region_metrics(self, region_id: str) -> Optional[Dict[str, Any]]:
        state = self._get_state()
        return state.get("regions", {}).get(region_id)

    def get_all_regions(self) -> Dict[str, Any]:
        state = self._get_state()
        return state.get("regions", {})

    def get_healthy_region_count(self, threshold_seconds: int = 15) -> int:
        regions = self.get_all_regions()
        count = 0
        now = datetime.now(timezone.utc)
        for rid, data in regions.items():
            updated_at_str = data.get("updated_at")
            if not updated_at_str:
                continue
            try:
                updated_at = datetime.fromisoformat(updated_at_str)
                if updated_at.tzinfo is None:
                    updated_at = updated_at.replace(tzinfo=timezone.utc)
                if (now - updated_at).total_seconds() <= threshold_seconds:
                    if data.get("health_score", 0) > 0.5:
                        count += 1
            except Exception:
                continue
        return count

    def is_quorum_maintained(self) -> bool:
        state = self._get_state()
        regions = state.get("regions", {})
        total_known_regions = len(regions)
        if total_known_regions == 0:
            return True
        
        healthy_count = self.get_healthy_region_count()
        return healthy_count > (total_known_regions / 2)

    def get_all_metrics(self) -> Dict[str, Any]:
        """Retrieves the full mesh state."""
        return self._get_state()

# Global Singleton for the Mesh
mesh_state_store = MeshStateStore()
