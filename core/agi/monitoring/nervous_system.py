import os
import psutil
import time
from typing import Dict, Any, Optional
from memory.store import memory_store
from sqlalchemy.ext.asyncio import AsyncSession
from observability.logging import get_logger

_log = get_logger("agi_nervous_system")

class NervousSystem:
    """
    Monitoring Core (Katman 15): Sensory Hub / Nervous Pulse.
    Sistemin operasyonel 'Sağlığını' (Pulse) sürekli izler ve bilişsel merkeze iletir.
    """
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        # Bilişsel metrikler (Faz 13.3)
        self.cognitive_metrics = {
            "success_rate": 1.0,
            "total_tasks": 0,
            "successful_tasks": 0,
            "tool_reliability": {},
            "correction_count": 0
        }

    async def pulse(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Sistemin anlık sinirsel verilerini toplar.
        """
        try:
            # 1. Kaynak Kullanımı
            mem_info = self.process.memory_info()
            cpu_usage = self.process.cpu_percent(interval=0.1)
            
            # 2. Operasyonel Metrikler (Placeholder)
            # Gelecekte buraya DB latency, Redis speed vb. eklenebilir.
            
            sensory_data = {
                "cpu_percent": cpu_usage,
                "memory_rss_mb": mem_info.rss / 1024 / 1024,
                "timestamp": time.time(),
                "status": "healthy" if cpu_usage < 80 else "stressed",
                "cognitive": self.cognitive_metrics
            }
            
            # 3. Belleğe Kaydet (Sensory)
            await memory_store.save(
                db=db,
                agent_id="nervous_system",
                body=f"Pulse: CPU={cpu_usage}%, RAM={sensory_data['memory_rss_mb']:.1f}MB",
                category="sensory_input",
                importance=0.4,
                metadata=sensory_data,
                tags=["telemetry", "health"]
            )
            
            _log.info(f"SİSTEM NABZI (Pulse): {sensory_data['status'].upper()} | CPU: {cpu_usage}%")
            return sensory_data

        except Exception as e:
            _log.error(f"Nervous pulse hatası: {e}")
            return {"status": "unknown", "error": str(e)}

    def check_stress(self, metrics: Dict[str, Any]) -> bool:
        """Sistemin 'Stres' altında olup olmadığını değerlendirir."""
        return metrics.get("status") == "stressed"

    def log_cognitive_event(self, event_type: str, success: bool, detail: str = ""):
        """
        Bilişsel bir olayı kaydeder ve metrikleri günceller.
        """
        self.cognitive_metrics["total_tasks"] += 1
        if success:
            self.cognitive_metrics["successful_tasks"] += 1
        
        # Başarı oranını güncelle
        if self.cognitive_metrics["total_tasks"] > 0:
            self.cognitive_metrics["success_rate"] = self.cognitive_metrics["successful_tasks"] / self.cognitive_metrics["total_tasks"]
        
        if "correction" in event_type.lower():
            self.cognitive_metrics["correction_count"] += 1
            
        _log.debug(f"Bilişsel Olay: {event_type} | Başarı: {success} | Detay: {detail}")

# --- Singleton ---
nervous_system = NervousSystem()
