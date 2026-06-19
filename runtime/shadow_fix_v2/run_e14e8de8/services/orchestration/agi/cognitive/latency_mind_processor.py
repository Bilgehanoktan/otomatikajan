import asyncio
import json
from typing import Optional, List, Dict, Any
from services.observability.logging import get_logger
from libs.llm.model_orchestrator import model_orchestrator
from libs.db.session import session_scope
from sqlalchemy import select, desc
from libs.db.models import SubTask, ProjectStatus, ImprovementOpportunity

_log = get_logger("agi_latency_mind")

class LatencyMindProcessor:
    """
    Cognitive Core (Katman 31): Latency Mind Processor (Gecikmeli Zihin İşlemcisi).
    İşlem döngüsü (Mind Cycle) bloklamayacak şekilde, arka planda (async task) çalışarak
    kendi kendine hedefler çıkarır, hafızayı sıkıştırır veya kod yapısını 'hayal eder'.
    """
    def __init__(self):
        self._is_dreaming = False

    async def _dream_task(self):
        """Asıl arka plan işlemi. AGI burada rölantideyken kendi üstüne düşünür."""
        try:
            self._is_dreaming = True
            _log.info("Gecikmeli Zihin (Latency Mind): 'Düşünce' durumu başladı... Sistem optimize yolları arıyor.")
            
            async with session_scope() as db:
                # 1. Son hataları topla
                result = await db.execute(
                    select(SubTask)
                    .where(SubTask.status == ProjectStatus.ERROR)
                    .order_by(desc(SubTask.created_at))
                    .limit(5)
                )
                failed_tasks = result.scalars().all()
                
                if not failed_tasks:
                    _log.info("Gecikmeli Zihin: Analiz edilecek kritik hata bulunamadı. İşlem sonlanıyor.")
                    return

                # 2. LLM'e 'Rüya Sentezi' yaptır
                error_context = "\n".join([f"- Agent: {t.agent_id} | Error: {t.result[:200]}" for t in failed_tasks])
                
                prompt = f"""
                Sistemin gecikmeli zihni (latency mind) olarak son başarısızlıkları analiz et:
                {error_context}
                
                Bu hataların ortak bir kök nedeni var mı? Gelecekte nasıl önlenebilir?
                Lütfen bir 'İyileştirme Fırsatı' (Improvement Opportunity) tanımla.
                
                JSON Format:
                {{
                    "title": "Kısa Başlık",
                    "description": "Detaylı analiz",
                    "severity": "high/medium/low",
                    "category": "reliability/performance/security"
                }}
                """
                
                response = await model_orchestrator.complete_task(
                    agent_role="architect",
                    prompt=prompt,
                    system_prompt="Sen bir AGI Gecikmeli Zihnisin (Latency Mind). Sistemin hatalarından ders çıkarmasını sağlarsın."
                )
                
                # 3. İçgörüyü Kaydet
                try:
                    data = self._parse_json(response.content)
                    if data:
                        from libs.db.repositories.repository import ImprovementRepository
                        await ImprovementRepository.create(
                            db=db,
                            source_type="latency_mind_dream",
                            title=f"[LATENCY] {data.get('title')}",
                            description=data.get('description'),
                            severity=data.get('severity', 'medium'),
                            category=data.get('category', 'reliability')
                        )
                        _log.info(f"Gecikmeli Zihin: Yeni bir içgörü sentezlendi ve kaydedildi: {data.get('title')}")
                except Exception as e:
                    _log.error(f"Insight parsing failed: {e}")

            await asyncio.sleep(1.0) # Küçük bir soğuma süresi
            
        except asyncio.CancelledError:
            _log.warning("Gecikmeli Zihin: Ani uyanış! Arka plan işlemi kesildi.")
        except Exception as e:
            _log.error(f"Gecikmeli Zihin hatası: {e}")
        finally:
            self._is_dreaming = False

    def _parse_json(self, content: str) -> Optional[Dict[str, Any]]:
        try:
            import re
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception:
            pass
        return None

    def spawn_dream_thread(self):
        """
        Ana zihin döngüsünü (Main Thread) bloklamadan (fire-and-forget), 
        arka planda bağımsız bir gecikmeli zihin işlemini tetikler.
        """
        if self._is_dreaming:
            return
            
        _log.info("Gecikmeli Zihin: Uygun duygu durumu tespit edildi. Arka plan işlemi tetikleniyor.")
        asyncio.create_task(self._dream_task())

# Singleton
latency_mind_processor = LatencyMindProcessor()
