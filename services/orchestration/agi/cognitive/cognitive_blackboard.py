import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from libs.db.session import get_redis_client

logger = logging.getLogger("agi_blackboard")

class CognitiveBlackboard:
    """
    AGI 'Çalışma Belleği' (Working Memory).
    Bir hedefin (Goal) yaşam süresi boyunca agentlar arası hızlı bilgi transferini sağlar.
    'State Awareness' ve 'Context Persistence' (Hafıza Bütünlüğü) için kritiktir.
    """

    def __init__(self, goal_id: str):
        self.goal_id = goal_id
        self.redis = get_redis_client()
        self._key = f"agi:blackboard:{goal_id}"

    async def post_discovery(self, source_agent: str, discovery: str, confidence: float = 1.0):
        """Yeni bir keşif (Bilgi) ekle."""
        record = {
            "type": "discovery",
            "agent": source_agent,
            "content": discovery,
            "confidence": confidence,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self._push_to_list("discoveries", record)
        logger.info(f"[BLACKBOARD] Keşif Eklendi ({source_agent}): {discovery[:50]}...")

    async def post_warning(self, source_agent: str, warning: str, severity: str = "medium"):
        """Sistemi belirli bir kısıtlama veya hata olasılığına karşı uyar."""
        record = {
            "type": "warning",
            "agent": source_agent,
            "content": warning,
            "severity": severity,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self._push_to_list("warnings", record)
        logger.warning(f"[BLACKBOARD] Uyarı Eklendi ({source_agent}): {warning}")

    async def set_hypothesis(self, source_agent: str, hypothesis: str):
        """Mevcut sorun için bir varsayım (çözüm yolu) belirle."""
        record = {
            "agent": source_agent,
            "content": hypothesis,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self._set_hash("active_hypothesis", record)

    async def get_working_context(self) -> Dict[str, Any]:
        """Ajanların kullanımı için tüm 'Aktif Hafıza' yı özet olarak döner."""
        if not self.redis: return {}
        
        discoveries = await self._get_list("discoveries")
        warnings = await self._get_list("warnings")
        hypothesis = await self._get_hash("active_hypothesis")
        
        return {
            "goal_id": self.goal_id,
            "active_discoveries": discoveries[-10:], # Son 10 keşif
            "critical_warnings": warnings[-5:],    # Son 5 uyarı
            "current_hypothesis": hypothesis
        }

    async def clear(self):
        """Hafızayı temizle (Görev bittiğinde)."""
        if self.redis:
            await self.redis.delete(self._key)

    # ── Internal Helpers ─────────────────────────────────────
    async def _push_to_list(self, subkey: str, data: dict):
        if not self.redis: return
        full_key = f"{self._key}:{subkey}"
        await self.redis.rpush(full_key, json.dumps(data))
        await self.redis.expire(full_key, 3600 * 24) # 24 saat TTL

    async def _get_list(self, subkey: str) -> List[dict]:
        if not self.redis: return []
        full_key = f"{self._key}:{subkey}"
        items = await self.redis.lrange(full_key, 0, -1)
        return [json.loads(i) for i in items]

    async def _set_hash(self, subkey: str, data: dict):
        if not self.redis: return
        full_key = f"{self._key}:{subkey}"
        await self.redis.set(full_key, json.dumps(data))
        await self.redis.expire(full_key, 3600 * 24)

    async def _get_hash(self, subkey: str) -> Optional[dict]:
        if not self.redis: return None
        full_key = f"{self._key}:{subkey}"
        data = await self.redis.get(full_key)
        return json.loads(data) if data else None

# Helper function to get blackboard for a task
def get_blackboard(goal_id: str) -> CognitiveBlackboard:
    return CognitiveBlackboard(goal_id)
