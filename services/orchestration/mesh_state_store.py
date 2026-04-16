"""
Sovereign AGI — Phase 20
services/orchestration/mesh_state_store.py
A persistent state store for mesh-wide metrics (Health, Latency).
Simulates a distributed KV store (Redis) for pilot environments.
"""
from __future__ import annotations
import json
import os
import threading
from typing import Dict, Any, Optional
from datetime import datetime

class MeshStateStore:
    def __init__(self, storage_path: str = "configs/mesh_state.json"):
        self.storage_path = storage_path
        self._lock = threading.Lock()
        self._state: Dict[str, Any] = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        if not os.path.exists(self.storage_path):
            return {
                "regions": {},
                "last_update": datetime.utcnow().isoformat(),
                "version": "1.0"
            }
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"regions": {}, "last_update": datetime.utcnow().isoformat()}

    def _save_state(self):
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(self._state, f, indent=2)

    def set_region_metrics(self, region_id: str, metrics: Dict[str, Any]):
        """Updates metrics for a specific region."""
        with self._lock:
            if region_id not in self._state["regions"]:
                self._state["regions"][region_id] = {}
            
            # Merge metrics
            self._state["regions"][region_id].update(metrics)
            self._state["regions"][region_id]["updated_at"] = datetime.utcnow().isoformat()
            self._state["last_update"] = datetime.utcnow().isoformat()
            self._save_state()

    def get_region_metrics(self, region_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves metrics for a region."""
        with self._lock:
            return self._state["regions"].get(region_id)

    def get_healthy_region_count(self, threshold_seconds: int = 15) -> int:
        """Returns the number of regions that have pulsed within the threshold."""
        count = 0
        now = datetime.utcnow()
        with self._lock:
            for rid, data in self._state["regions"].items():
                updated_at_str = data.get("updated_at")
                if not updated_at_str:
                    continue
                
                updated_at = datetime.fromisoformat(updated_at_str)
                if (now - updated_at).total_seconds() <= threshold_seconds:
                    count += 1
        return count

    def get_active_regions(self, threshold_seconds: int = 15) -> list[str]:
        """Returns IDs of regions currently considered 'Alive'."""
        active = []
        now = datetime.utcnow()
        with self._lock:
            for rid, data in self._state["regions"].items():
                updated_at = datetime.fromisoformat(data.get("updated_at", ""))
                if (now - updated_at).total_seconds() <= threshold_seconds:
                    active.append(rid)
        return active

    def is_quorum_maintained(self) -> bool:
        """Checks if the mesh currently has at least floor(N/2) + 1 healthy regions."""
        with self._lock:
            total_known_regions = len(self._state["regions"])
            if total_known_regions == 0:
                return True # Bootstrap edge case
        
        healthy_count = self.get_healthy_region_count()
        quorum_required = (total_known_regions // 2) + 1
        return healthy_count >= quorum_required

    def get_all_metrics(self) -> Dict[str, Any]:
        """Retrieves the full mesh state."""
        with self._lock:
            return self._state

# Global Singleton for the Mesh
mesh_state_store = MeshStateStore()
