"""
Watchdog Log Aggregation (Vector Memory)
Sistem olaylarını ve iyileştirme kayıtlarını vektör veri tabanına (MemoryStore) işler.
"""
from typing import Any
from packages.orchestration.agi.cognitive.synaptic_cortex import synaptic_cortex as memory_store
from db.session import AsyncSessionLocal
from observability.logging import get_logger

logger = get_logger("memory.watchdog")

class VectorWatchdog:
    def __init__(self):
        self.category = "system_event"

    async def log_event(self, agent_id: str, severity: str, phase: str, message: str, metadata: dict | None = None):
        """Kritik bir olayı vektör belleğine kaydeder."""
        try:
            # Sadece WARNING ve CRITICAL olayları kalıcı belleğe (RAG) ekle
            if severity not in ("warning", "critical"):
                return

            importance = 0.8 if severity == "critical" else 0.5
            body = f"[{severity.upper()}][{phase}] {agent_id}: {message}"
            
            async with AsyncSessionLocal() as db:
                await memory_store.save(
                    db=db,
                    agent_id=agent_id,
                    body=body,
                    category=self.category,
                    importance=importance,
                    metadata={
                        "phase": phase,
                        "severity": severity,
                        **(metadata or {})
                    }
                )
                await db.commit()
                # logger.debug(f"Event vectorized: {body}")
        except Exception as e:
            logger.error(f"VectorWatchdog error: {e}")

    async def search_events(self, query: str, top_k: int = 5):
        """Geçmiş sistem anomalilerini semantik olarak ara."""
        async with AsyncSessionLocal() as db:
            return await memory_store.search(
                db=db,
                query=query,
                category=self.category,
                top_k=top_k
            )

watchdog = VectorWatchdog()
