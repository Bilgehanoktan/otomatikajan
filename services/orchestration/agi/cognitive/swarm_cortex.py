import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from services.observability.logging import get_logger

_log = get_logger("agi_hive_memory")

class SwarmCortex:
    """
    Cognitive Core (Katman 20): Swarm Cortex.
    Sürü birimleri arasında paylaşılan global bellek ve durum alanı (former Hive Memory).
    """
    def __init__(self) -> None:
        self.shared_state: Dict[str, Any] = {
            "active_units": [],
            "global_context": "",
            "hive_priority": "standard",
            "collective_wisdom_cache": {},
            "last_sync": datetime.now(timezone.utc).isoformat()
        }

    async def register_unit(self, unit_id: str, capabilities: List[str]):
        """Bir sürü birimini (Swarm Unit) kovana kaydeder."""
        active_units: List[Dict[str, Any]] = self.shared_state["active_units"]
        if unit_id not in [u["id"] for u in active_units]:
            active_units.append({
                "id": unit_id,
                "capabilities": capabilities,
                "status": "ready",
                "last_seen": datetime.now(timezone.utc).isoformat()
            })
            _log.info(f"[SWARM] Unit Kayıt Edildi: {unit_id}")

    async def update_hive_context(self, context_update: str):
        """Sürünün global bağlamını günceller."""
        self.shared_state["global_context"] = context_update
        self.shared_state["last_sync"] = datetime.now(timezone.utc).isoformat()
        _log.info("[SWARM] Context Güncellendi.")

    def get_available_units(self, required_capability: str) -> List[str]:
        """Belirli bir yeteneğe sahip boşta olan birimleri döndürür."""
        active_units: List[Dict[str, Any]] = self.shared_state["active_units"]
        return [
            u["id"] for u in active_units 
            if required_capability in u["capabilities"] and u["status"] == "ready"
        ]

    def dump_state(self) -> str:
        """Sürünün anlık durumunu JSON olarak döner."""
        return json.dumps(self.shared_state, indent=2)

# Singleton Instance
swarm_cortex = SwarmCortex()

# Compatibility Aliases
HiveMemory = SwarmCortex
hive_memory = swarm_cortex
