import asyncio
import os
import json
import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

from sqlalchemy import select, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import Memory, ProjectStatus, Project, SubTask
from db.session import session_scope
from db.repository import ProjectRepository
from packages.orchestration.agi.learning.wisdom_synthesizer import wisdom_synthesizer
from llm.model_orchestrator import ModelOrchestrator
from observability.logging import get_logger

_log = get_logger("agi_dream_engine")

class DreamEngine:
    """
    Cognitive Core (Katman 59): Dream Cycle & Memory Consolidation.
    Sistemin 'Uyku' (Hafıza Temizliği, Sıkıştırma ve Bilgelik Sentezi) döngüsünü yönetir.
    Redundant veriyi temizler, operasyonel hafızayı stratejik KI'lara dönüştürür.
    """

    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()
        self.knowledge_dir = "knowledge"
        os.makedirs(self.knowledge_dir, exist_ok=True)
        self.is_dreaming = False
        
        # Sıkıştırma Konfigürasyonu
        self.min_importance = 0.2
        self.noise_age_hours = 48
        self.consolidation_threshold = 3 

    # --- PART 1: Memory Pruning & Consolidation (from MemoryPruner) ---

    async def run_dream_cycle(self, db: AsyncSession):
        """Ana bilişsel temizlik ve rüya döngüsü. (Consolidated v12.1)"""
        if self.is_dreaming:
            _log.info("[DREAM] Zaten bir rüya döngüsü devam ediyor.")
            return

        self.is_dreaming = True
        _log.info("--- SOVEREIGN DREAM CYCLE STARTED ---")
        
        try:
            # 1. Gürültü Temizliği (Pruning)
            await self.prune_noise(db)
            
            # 2. Benzer Anıları Konsolide Et (Hafıza Sentezi)
            await self.consolidate_memories(db)
            
            # 3. Bölüm Analizi ve Politika Sentezi (from SubconsciousCortex45)
            await self.synthesize_policies(db)
            
            # 4. Proje Bazlı Bilgi Sentezi (Knowledge Item Generation)
            await self.synthesize_knowledge_items(db)
            
            _log.info("--- SOVEREIGN DREAM CYCLE COMPLETED ---")
        except Exception as e:
            _log.error(f"[DREAM] Rüya döngüsü hatası: {e}")
        finally:
            self.is_dreaming = False

    async def synthesize_policies(self, db: AsyncSession):
        """Bölümler (Episodes) arasındaki örüntüleri bulur ve politikalar sentezler."""
        from packages.orchestration.agi.cognitive.synaptic_cortex import synaptic_cortex
        
        # Son bölümleri (Episodes) getir
        recent_episodes = await synaptic_cortex.get_recent(db, category="episode_record", limit=20)
        if len(recent_episodes) < 5:
            return

        _log.info(f"[DREAM-POLICY] {len(recent_episodes)} bölüm analiz ediliyor...")
        
        history_str = "\n".join([
            f"- Title: {e.metadata_.get('title', 'N/A')} | Status: {e.metadata_.get('status', 'N/A')} | Summary: {e.body[:100]}"
            for e in recent_episodes
        ])

        prompt = f"GÖREV GEÇMİŞİ:\n{history_str}\n\nLütfen bu tecrübelerden 'Evrensel Dersler' ve 'POLİTİKALAR' sentezle. JSON: {{'lessons': [], 'policies': [{{'title': '...', 'rule': '...', 'reason': '...'}}]}}"
        
        try:
            response = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt="Sen AGI Bilinçaltı Politika Sentezleyicisisin."
            )
            import re
            match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if match:
                data = json.loads(match.group())
                for policy in data.get("policies", []):
                    # Kısmi kopya: synaptic_cortex.save_policy
                    _log.info(f"[DREAM-POLICY] Yeni politika önerildi: {policy.get('title')}")
                    await synaptic_cortex.save(
                        db, agent_id="dream_engine", body=policy.get("rule"),
                        category="policy_proposal", importance=0.8,
                        metadata={
                            "proposed_rule": policy.get("rule"),
                            "reason": policy.get("reason"),
                            "title": policy.get("title"),
                            "status": "pending"
                        }
                    )
        except Exception as e:
            _log.warning(f"[DREAM-POLICY] Politika sentez hatası: {e}")

    async def prune_noise(self, db: AsyncSession):
        """Düşük öncelikli ve eski anıları temizler."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=self.noise_age_hours)
        
        stmt = delete(Memory).where(
            and_(
                Memory.importance < self.min_importance,
                Memory.created_at < cutoff,
                Memory.category != "semantic_wisdom" 
            )
        )
        result = await db.execute(stmt)
        await db.commit()
        if result.rowcount > 0:
            _log.info(f"[DREAM-PRUNE] {result.rowcount} adet gürültü kaydı temizlendi.")

    async def consolidate_memories(self, db: AsyncSession):
        """Tekrarlayan anıları 'Master Wisdom' paketlerine dönüştürür."""
        stmt = select(Memory.category, func.count(Memory.id)).group_by(Memory.category).having(func.count(Memory.id) >= self.consolidation_threshold)
        categories = (await db.execute(stmt)).all()
        
        for category, count in categories:
            if category == "semantic_wisdom": continue

            mem_stmt = select(Memory).where(Memory.category == category).order_by(Memory.created_at.desc()).limit(10)
            memories = (await db.execute(mem_stmt)).scalars().all()
            
            if len(memories) < self.consolidation_threshold: continue

            _log.info(f"[DREAM-CONSOLIDATE] '{category}' kategorisinde {len(memories)} anı birleştiriliyor.")
            
            # WisdomSynthesizer uyumlu mock task
            from packages.orchestration.agi.task_governance import ProjectTask as GovernanceTask, SubTask as GovernanceSubTask, TaskStatus
            mock_task = GovernanceTask(
                id=f"dream-merge-{category}",
                title=f"Consolidated Memory: {category}",
                description=f"Merging {len(memories)} granular experiences into a unified pattern."
            )
            mock_task.subtasks = [
                GovernanceSubTask(id=str(m.id), agent_id=m.agent_id, prompt="N/A", result=m.body, status=TaskStatus.COMPLETED)
                for m in memories
            ]
            
            wisdom = await wisdom_synthesizer.synthesize_from_task(mock_task)
            if wisdom:
                ids_to_delete = [m.id for m in memories]
                await db.execute(delete(Memory).where(Memory.id.in_(ids_to_delete)))
                await db.commit()
                _log.info(f"[DREAM-CONSOLIDATE] {len(ids_to_delete)} anı tek bir bilgi paketine dönüştürüldü.")

    # --- PART 2: Strategic Knowledge Synthesis (from Consolidator) ---

    async def synthesize_knowledge_items(self, db: AsyncSession):
        """Tamamlanan projeleri analiz eder ve kalıcı MD dosyaları (KI) sentezler."""
        projects = await ProjectRepository.list_recent(db, limit=5, status=ProjectStatus.COMPLETED.value)
        
        for project in projects:
            # Daha önce konsolide edilip edilmediğini kontrol et (Basit metadata kontrolü)
            if project.metadata_.get("consolidated"): continue
            
            _log.info(f"[DREAM-KI] Proje stratejik bilgiye dönüştürülüyor: {project.title}")
            
            prompt = f"PROJE: {project.title}\nRAPOR: {project.report}\n\nBu projeden 'Altın Kurallar' ve 'Hata Desenleri' çıkar (JSON): {{'ki_title': '...', 'category': '...', 'lessons_learned': [], 'anti_patterns': []}}"
            try:
                response = await self.model_orch.complete_task(
                    agent_role="consolidator",
                    prompt=prompt,
                    system_prompt="Sen bir AGI Hafıza Stratejistisin."
                )
                import re
                match = re.search(r'\{.*\}', response.content, re.DOTALL)
                if match:
                    ki_data = json.loads(match.group())
                    await self._write_ki_file(ki_data, str(project.id))
                    project.metadata_ = {**project.metadata_, "consolidated": True}
                    await db.commit()
            except Exception as e:
                _log.error(f"[DREAM-KI] KI sentez hatası ({project.id}): {e}")

    async def _write_ki_file(self, data: Dict[str, Any], source_id: str):
        ki_id = str(uuid.uuid4())[:8]
        filename = f"ki_{data.get('category', 'gen')}_{ki_id}.md"
        path = os.path.join(self.knowledge_dir, filename)
        
        content = f"# Knowledge Item: {data.get('ki_title')}\n\n" \
                  f"- **Source**: {source_id}\n" \
                  f"- **Date**: {datetime.now(timezone.utc).isoformat()}\n\n" \
                  f"## Lessons Learned\n" + "\n".join([f"- {l}" for l in data.get('lessons_learned', [])]) + \
                  f"\n\n## Anti-Patterns\n" + "\n".join([f"- {a}" for a in data.get('anti_patterns', [])])
        
        with open(path, "w", encoding="utf-8") as f: f.write(content)
        _log.info(f"[DREAM-KI] Yeni KI dosyası: {filename}")

    # --- PART 3: Context Compaction (from Compactor) ---

    async def compact_context(self, history: List[Any], current_goal: str) -> str:
        """Aksiyon geçmişini yüksek seviyeli bir özete sıkıştırır."""
        if not history: return "No history yet."
        
        _log.info(f"[DREAM-COMPACT] Context sıkıştırılıyor: {len(history)} kayıt.")
        history_str = "\n".join([f"{i+1}. {h.tool_used}: {'Success' if h.success else 'Fail'}" for i, h in enumerate(history)])
        prompt = f"GÖREV: {current_goal}\nGEÇMİŞ:\n{history_str}\n\nÖnemli sonuçları ve engelleri özetle."
        
        try:
            resp = await self.model_orch.complete_task(agent_role="analyst", prompt=prompt)
            return resp.content
        except Exception as e:
            _log.error(f"[DREAM-COMPACT] Compaction failed: {e}")
            return "Compaction failed."

# Singleton
dream_engine = DreamEngine()

async def start_dream_loop():
    """Background metabolism loop with adaptive sleep."""
    from packages.orchestration.agi.monitoring.token_budgeter import token_budgeter
    while True:
        try:
            health = await token_budgeter.check_health()
            score = health.get("health_score", 1.0)
            
            # Skor düştükçe uyku süresi artar (0.8+ -> 6s, 0.4+ -> 24s, 0.4- -> 48s)
            delay = 3600 * (6 if score > 0.8 else (24 if score > 0.4 else 48))
            
            async with session_scope() as db:
                await dream_engine.run_dream_cycle(db)
            
            await asyncio.sleep(delay)
        except Exception as e:
            _log.error(f"[DREAM-LOOP] Error: {e}")
            await asyncio.sleep(600)
