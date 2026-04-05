import os
import psutil
import time
from typing import Dict, Any, Optional
from packages.orchestration.agi.cognitive.synaptic_cortex import synaptic_cortex as memory_store
from sqlalchemy.ext.asyncio import AsyncSession
from observability.logging import get_logger
from packages.orchestration.agi.monitoring.token_budgeter import token_budgeter
from packages.orchestration.agi.operational.resource_manager import resource_manager
from packages.orchestration.agi.cognitive.subconscious_cortex_45 import subconscious_cortex_45
from packages.orchestration.agi.adaptation.sovereign_evolution_45 import sovereign_evolution_45

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
            "correction_count": 0,
            "grounding_persistence": 1.0,
            "dissonance_alerts": 0
        }

    async def pulse(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Sistemin anlık sinirsel verilerini toplar.
        """
        try:
            # 1. Kaynak Kullanımı
            mem_info = self.process.memory_info()
            cpu_usage = self.process.cpu_percent(interval=0.1)
            
            # 3. Metabolizma (Faz 24)
            metabolism = await token_budgeter.check_health()
            
            # 4. Kaynak Tahmini (Faz 29)
            await resource_manager.update_status()
            resource_guidance = resource_manager.get_strategy_guidance()
            
            status = "healthy"
            if cpu_usage > 80 or metabolism["health_score"] < 0.5 or resource_guidance["mode"] != "OPTIMAL":
                status = "stressed" if resource_guidance["mode"] == "CONSERVATIVE" else "critical"
            
            sensory_data = {
                "cpu_percent": cpu_usage,
                "memory_rss_mb": mem_info.rss / 1024 / 1024,
                "timestamp": time.time(),
                "status": status,
                "cognitive": self.cognitive_metrics,
                "metabolism": metabolism,
                "resource_mode": resource_guidance["mode"]
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
            
            # --- Faz 45: Sovereign Cycle Tetikleme ---
            if status == "healthy" and cpu_usage < 15 and resource_guidance["mode"] == "OPTIMAL":
                import asyncio
                async def sovereign_cycle():
                    # 1. Dream (Reflect & Propose Policy)
                    await subconscious_cortex_45.dream(db)
                    # 2. Evolve (Synthesize & Apply Patch)
                    await sovereign_evolution_45.evolve_system(db)
                
                _log.info("[NERVOUS-SYSTEM] Sistem rölantide. Sovereign Cycle (Dream + Evolve) başlatılıyor...")
                asyncio.create_task(sovereign_cycle())
                
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

    def log_grounding_event(self, score: float, has_dissonance: bool):
        """Gerçeklik doğrulama skorunu ve çelişki olaylarını kaydeder."""
        # Rolling average (p=0.2)
        current = self.cognitive_metrics.get("grounding_persistence", 1.0)
        self.cognitive_metrics["grounding_persistence"] = round((current * 0.8) + (score * 0.2), 3)
        
        if has_dissonance:
            self.cognitive_metrics["dissonance_alerts"] += 1
            _log.warning(f"[NS-GROUNDING] Bilişsel Çelişki Bildirildi! Toplam: {self.cognitive_metrics['dissonance_alerts']}")

# --- Singleton ---
nervous_system = NervousSystem()
