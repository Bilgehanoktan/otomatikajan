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

    # Process-wide in-memory fallback for Degraded Mode (no Redis)
    _memory_fallback: Dict[str, Dict[str, Any]] = {}

    def __init__(self, goal_id: str):
        self.goal_id = goal_id
        self._key = f"agi:blackboard:{goal_id}"
        if goal_id not in CognitiveBlackboard._memory_fallback:
            CognitiveBlackboard._memory_fallback[goal_id] = {
                "discoveries": [],
                "warnings": [],
                "active_hypothesis": None
            }

    async def _get_redis(self):
        """Asenkron olarak Redis istemcisini döner."""
        return await get_redis_client()

    async def post_discovery(self, source_agent: str, discovery: str, confidence: float = 1.0):
        """Yeni bir keşif (Bilgi) ekle."""
        record = {
            "type": "discovery",
            "agent": source_agent,
            "content": discovery,
            "confidence": confidence,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        redis = await self._get_redis()
        if redis:
            await self._push_to_list("discoveries", record)
        else:
            # Fallback to in-memory
            CognitiveBlackboard._memory_fallback[self.goal_id]["discoveries"].append(record)
            
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
        redis = await self._get_redis()
        if redis:
            await self._push_to_list("warnings", record)
        else:
            CognitiveBlackboard._memory_fallback[self.goal_id]["warnings"].append(record)

        logger.warning(f"[BLACKBOARD] Uyarı Eklendi ({source_agent}): {warning}")

    async def set_hypothesis(self, source_agent: str, hypothesis: str):
        """Mevcut sorun için bir varsayım (çözüm yolu) belirle."""
        record = {
            "agent": source_agent,
            "content": hypothesis,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        redis = await self._get_redis()
        if redis:
            await self._set_hash("active_hypothesis", record)
        else:
            CognitiveBlackboard._memory_fallback[self.goal_id]["active_hypothesis"] = record

    async def get_working_context(self) -> Dict[str, Any]:
        """Ajanların kullanımı için tüm 'Aktif Hafıza' yı özet olarak döner."""
        redis = await self._get_redis()
        if redis:
            discoveries = await self._get_list("discoveries")
            warnings = await self._get_list("warnings")
            hypothesis = await self._get_hash("active_hypothesis")
        else:
            mem = CognitiveBlackboard._memory_fallback.get(self.goal_id, {})
            discoveries = mem.get("discoveries", [])
            warnings = mem.get("warnings", [])
            hypothesis = mem.get("active_hypothesis")
        
        return {
            "goal_id": self.goal_id,
            "active_discoveries": discoveries[-10:], # Son 10 keşif
            "critical_warnings": warnings[-5:],    # Son 5 uyarı
            "current_hypothesis": hypothesis
        }

    async def clear(self):
        """Hafızayı temizle (Görev bittiğinde)."""
        redis = await self._get_redis()
        if redis:
            await redis.delete(self._key)
        
        if self.goal_id in CognitiveBlackboard._memory_fallback:
            del CognitiveBlackboard._memory_fallback[self.goal_id]

    # ── Internal Helpers ─────────────────────────────────────
    async def _push_to_list(self, subkey: str, data: dict):
        redis = await self._get_redis()
        if not redis: return
        full_key = f"{self._key}:{subkey}"
        await redis.rpush(full_key, json.dumps(data))
        await redis.expire(full_key, 3600 * 24) # 24 saat TTL

    async def _get_list(self, subkey: str) -> List[dict]:
        redis = await self._get_redis()
        if not redis: return []
        full_key = f"{self._key}:{subkey}"
        items = await redis.lrange(full_key, 0, -1)
        return [json.loads(i) for i in items]

    async def _set_hash(self, subkey: str, data: dict):
        redis = await self._get_redis()
        if not redis: return
        full_key = f"{self._key}:{subkey}"
        await redis.set(full_key, json.dumps(data))
        await redis.expire(full_key, 3600 * 24)

    async def _get_hash(self, subkey: str) -> Optional[dict]:
        redis = await self._get_redis()
        if not redis: return None
        full_key = f"{self._key}:{subkey}"
        data = await redis.get(full_key)
        return json.loads(data) if data else None

# Helper function to get blackboard for a task
def get_blackboard(goal_id: str) -> CognitiveBlackboard:
    return CognitiveBlackboard(goal_id)
