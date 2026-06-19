import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from services.orchestration.agi.task_governance import ProjectTask, SubTask, TaskStatus
from libs.llm.model_orchestrator import ModelOrchestrator
from services.orchestration.agi.cognitive.synaptic_cortex import synaptic_cortex

from services.orchestration.agi.world.causal_error_graph import causal_error_graph
from services.orchestration.agi.operational.metabolic_governor import metabolic_governor, MetabolicMode

_log = logging.getLogger("agi_wisdom_synthesizer")

class WisdomSynthesizer:
    """
    [Katman 53/54] Bilgelik Sentezleyicisi (Wisdom Synthesizer).
    Tamamlanan görevlerden stratejik dersler ve nedensel bağlar (Causal Links) çıkarır.
    """

    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()

    async def synthesize_from_task(self, task: ProjectTask) -> Optional[str]:
        """
        Bir projenin alt görevlerini analiz ederek 'Bilişsel Altın Küreler' ve 
        'Nedensel Hata Örüntüleri' üretir.
        """
        _log.info(f"[WISDOM] Görevden ders ve neden çıkarılıyor: {task.title}")

        # 1. Görev özetini ve sonuçları derle
        completed_steps = [st for st in task.subtasks if st.status == TaskStatus.COMPLETED]
        failed_steps = [st for st in task.subtasks if st.status == TaskStatus.ERROR]
        
        if not completed_steps and not failed_steps:
            return None

        traces = []
        for st in task.subtasks:
            traces.append(f"Ajan: {st.agent_id} | Adım: {st.id}\nDurum: {st.status}\nSonuç: {st.result}\nİçsel Monolog: {getattr(st, 'internal_monologue', 'N/A')}")

        full_trace = "\n---\n".join(traces[:10]) 

        # --- Phase 60.6: Saturation & Metabolic Gating ---
        is_saturated, existing_wisdom = await self._check_saturation(task)
        if is_saturated:
            _log.info(f"[WISDOM-SATURATION] Benzer ders zaten mevcut, sentez atlanyor: {task.title}")
            if existing_wisdom:
                # Grevin importance skorunu ve tekrar saysn artr
                await self._increment_importance(existing_wisdom)
            return "SATURATED" # Atlandn belirt

        # 2. LLM ile Sentez (Semantic & Causal Compression)
        prompt = f"""
        # AGI BİLGELEK VE NEDENSELLİK SENTEZİ
        
        Aşağıdaki yürütme izlerini analiz et. 
        1. 'Evrensel Mimari Dersler' çıkar.
        2. 'NEDENSEL BAĞLAR' (CAUSAL LINKS) tespit et.
        
        GÖREV: {task.title}
        AÇIKLAMA: {task.description}
        
        YÜRÜTME İZLERİ:
        {full_trace}
        
        KURALLAR:
        - Yanıtı Türkçe ver.
        - Önce kısa dersleri listele.
        - Sonra [CAUSAL_LINKS] bloğu içinde şu formatta nedensellikleri yaz:
          CAUSE: [neden] -> EFFECT: [sonuç] | AGENT: [ajan_id] | TYPE: [hata/verimlilik] | FIX: [önerilen_aksiyon]
        """

        try:
            response = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt="Sen stratejik bir AGI mimarısın. Olaylar arasındaki görünmez nedensel bağları (causality) görmekte uzmansın.",
                task_id=task.id
            )
            
            content = response.content if response else ""
            
            if content:
                # 3. Bilgeliği Kaydet (Text)
                async with self._get_db() as db:
                    await synaptic_cortex.save(
                        db=db,
                        agent_id="wisdom_synthesizer",
                        body=content,
                        category="semantic_wisdom",
                        importance=0.8
                    )
                
                # 4. Nedensel Bağları Ayrıştır ve WorldModel'e Kaydet (Phase 54)
                await self._parse_and_record_causality(content, task.id)
                
                return content
        except Exception as e:
            _log.error(f"[WISDOM] Sentez/Nedensellik hatas: {e}")
        
        return None

    async def _check_saturation(self, task: ProjectTask) -> tuple[bool, Optional[Dict]]:
        """Benzer bir dersin zaten kaydedilip kaydedilmediğini kontrol eder."""
        try:
            async with self._get_db() as db:
                # Benzer kategorideki son 10 dersi getir
                existing = await synaptic_cortex.search(
                    db=db,
                    query=task.title,
                    category="semantic_wisdom",
                    top_k=5
                )
                
                # Metabolik Duruma Göre Eşik Belirle
                mode = metabolic_governor.get_mode()
                threshold = 0.75 if mode == MetabolicMode.ECO else 0.90
                
                for memory in existing:
                    # Faz 12.2: Gerçek semantik benzerlik
                    sim = await synaptic_cortex.check_semantic_similarity(
                        task.title + " " + task.description, 
                        memory["body"]
                    )
                    if sim >= threshold:
                        return True, memory
        except Exception as e:
            _log.warning(f"[WISDOM-SAT] Saturation check error: {e}")
        return False, None

    async def _increment_importance(self, memory_dict: Dict):
        """Mevcut bilgelik kaydının 'önem' ve 'tekrar' verisini günceller."""
        try:
            from libs.db.models import Memory
            from sqlalchemy import update
            async with self._get_db() as db:
                m_id = memory_dict.get("id")
                new_importance = min(memory_dict.get("importance", 0.5) + 0.1, 1.0) # +0.1 for ASE mode
                await db.execute(
                    update(Memory).where(Memory.id == m_id).values(
                        importance=new_importance,
                        updated_at=datetime.now(timezone.utc)
                    )
                )
                await db.commit()
                _log.info(f"[WISDOM] Importance increased for memory {m_id} to {new_importance}")
        except Exception as e:
            _log.warning(f"Importance güncelleme hatası: {e}")

    def _get_db(self):
        """Consolidated DB session getter for async operations."""
        from libs.db.session import AsyncSessionLocal
        return AsyncSessionLocal()

    async def _parse_and_record_causality(self, content: str, task_id: str):
        """[CAUSAL_LINKS] bloğundaki verileri WorldModel'e aktarır."""
        import re
        links = re.findall(r"CAUSE:\s*(.*?)\s*->\s*EFFECT:\s*(.*?)\s*\|\s*AGENT:\s*(.*?)\s*\|\s*TYPE:\s*(.*?)\s*\|\s*FIX:\s*(.*)", content)
        
        for cause, effect, agent, e_type, fix in links:
            _log.info(f"[CAUSAL-WORLD] Yeni bağ kaydediliyor: {agent} -> {e_type}")
            causal_error_graph.record_error(
                error_type=e_type.strip(),
                agent_id=agent.strip(),
                root_cause=cause.strip(),
                task_id=task_id,
                preventive_action=fix.strip(),
                metadata={"effect_desc": effect.strip()}
            )

# Singleton
wisdom_synthesizer = WisdomSynthesizer()
