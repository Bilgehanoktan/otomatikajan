import asyncio
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from observability.logging import get_logger
from packages.orchestration.agi.consciousness.affective_core import affective_core

_log = get_logger("kinetic_arbiter")

@dataclass(order=True)
class ArbiterRequest:
    priority: float
    timestamp: float
    agent_id: str = field(compare=False)
    task_id: str = field(compare=False)
    future: asyncio.Future = field(default_factory=lambda: asyncio.Future(), compare=False)

class KineticArbiter:
    """
    Faz 43: Kinetik Kaynak Dağıtıcı (Arbiter).
    Sistemin bilişsel yükünü (LLM çağrıları) yönetir, önceliklendirir ve 
    rate-limit felaketlerini önlemek için akış hızını (pacing) ayarlar.
    """
    
    # Ajan rollerine göre taban öncelik ağırlıkları
    ROLE_WEIGHTS = {
        "self_governor": 10.0,
        "security":       9.0,
        "architect":      8.0,
        "strategist":     7.0,
        "backend_dev":    5.0,
        "qa_engineer":    4.0,
        "tech_writer":    2.0,
        "general":        3.0
    }

    def __init__(self):
        self._queue: Optional[asyncio.PriorityQueue] = None
        self._running = False
        self._max_total_slots = 15  # Sistemsel tavan
        self._active_slots = 0
        self._provider_semaphores: Dict[str, asyncio.Semaphore] = {}
        self._worker_task: Optional[asyncio.Task] = None

    async def _ensure_queue(self):
        if self._queue is None:
            self._queue = asyncio.PriorityQueue()

    async def start(self):
        if not self._running:
            await self._ensure_queue()
            self._running = True
            self._worker_task = asyncio.create_task(self._arbitration_loop())
            _log.info("[ARBITER] Kinetik Kaynak Dağıtıcı aktif.")

    async def stop(self):
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
        self._queue = None  # Reset for next run
        _log.info("[ARBITER] Kinetik Kaynak Dağıtıcı durduruldu.")

    async def acquire_slot(self, agent_role: str, task_id: str) -> Any:
        """
        Bir görev için yürütme slotu talep eder. 
        Kuyruğa girer ve önceliğe göre onay ( Future) döner.
        """
        await self._ensure_queue()
        if not self._running:
            await self.start()

        # 1. Öncelik Hesapla (Düşük sayı = Yüksek öncelik)
        aff_state = affective_core.get_state_matrix()
        urgency = aff_state.get("urgency", 0.5)
        stress = aff_state.get("internal_stress", 0.2)
        
        base_weight = self.ROLE_WEIGHTS.get(agent_role, 3.0)
        # Formül: Ajan ağırlığı * (Urgency + Stress + 1.0)
        # Örn: Governor (10) * (0.8 + 0.5 + 1.0) = 23.0 -> Negatif yapıyoruz (-23.0) 
        # Çünkü PriorityQueue en küçük değeri önce çıkarır.
        priority_val = -(base_weight * (1.0 + urgency + stress))
        
        req = ArbiterRequest(priority=priority_val, timestamp=time.time(), agent_id=agent_role, task_id=task_id)
        
        await self._queue.put(req)
        _log.info(f"[ARBITER] Slot talebi QUEUE'ya eklendi: {agent_role} (Prio: {priority_val:.2f}, ID: {task_id})")
        
        return await req.future

    async def _arbitration_loop(self):
        """Kuyruktaki görevleri sistemsel kapasiteye göre serbest bırakır."""
        while self._running:
            try:
                if self._active_slots < self._max_total_slots:
                    # Kuyruktan en öncelikli işi al
                    req: ArbiterRequest = await self._queue.get()
                    _log.debug(f"[ARBITER] Kuyruktan POP edildi: {req.agent_id} (Prio: {req.priority:.2f}, ID: {req.task_id})")
                    
                    # Slotu onayla
                    self._active_slots += 1
                    req.future.set_result(True)
                    
                    # Küçük bir 'Kinetik Gecikme' ekle (Pacing)
                    # Çok yoğun stres varsa pacing kısalır, 429 sonrası uzar.
                    pacing = self._calculate_pacing()
                    await asyncio.sleep(pacing)
                else:
                    # Kapasite doluysa bekle
                    await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                _log.error(f"[ARBITER] Loop hatası: {e}")
                await asyncio.sleep(1)

    def _calculate_pacing(self) -> float:
        """Sistemin stresine göre istekler arası boşluğu ayarlar."""
        aff_state = affective_core.get_state_matrix()
        stress = aff_state.get("internal_stress", 0.2)
        energy = aff_state.get("energy_reserve", 1.0)
        
        # Temel 100ms gecikme
        base_pacing = 0.1
        
        # Enerji düşükse veya stres yüksekse yavaşla (Throttle)
        if energy < 0.3 or stress > 0.7:
            base_pacing = 0.5 + (stress * 1.5)
            
        return base_pacing

    def release_slot(self):
        """Görev bittiğinde slotu geri verir."""
        if self._active_slots > 0:
            self._active_slots -= 1

# --- Singleton ---
kinetic_arbiter = KineticArbiter()
