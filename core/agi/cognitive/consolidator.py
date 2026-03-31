import asyncio
import os
import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from observability.logging import get_logger
from llm.model_orchestrator import ModelOrchestrator
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import session_scope
from db.repository import ProjectRepository, TaskLogRepository

_log = get_logger("agi_consolidator")

class Consolidator:
    """
    Operasyonel hafızayı stratejik bilgiye dönüştüren 'Dream' döngüsü.
    Tamamlanan projeleri analiz eder ve kalıcı Bilgi Öğeleri (KI) sentezler.
    """
    
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()
        self.knowledge_dir = "knowledge"
        os.makedirs(self.knowledge_dir, exist_ok=True)

    async def run_consolidation_cycle(self, db: Optional[AsyncSession] = None):
        """Tüm sistemi tarar ve yeni bilgileri sentezler."""
        _log.info("[CONSOLIDATOR] Konsolidasyon döngüsü (Dream Cycle) başlatıldı.")
        
        if db:
            await self._process_cycle(db)
        else:
            async with session_scope() as new_db:
                await self._process_cycle(new_db)

    async def _process_cycle(self, db: AsyncSession):
        from db.models import ProjectStatus
        # 1. Tamamlanmış ancak konsolide edilmemiş projeleri bul
        projects = await ProjectRepository.list_recent(db, limit=10, status=ProjectStatus.COMPLETED.value)
        
        if not projects:
            _log.info("[CONSOLIDATOR] Konsolide edilecek yeni proje bulunamadı.")
            return

        for project in projects:
            await self._consolidate_project(project)

    async def _consolidate_project(self, project):
        """Münferit bir projeyi analiz eder ve KI oluşturur."""
        _log.info(f"[CONSOLIDATOR] Proje analiz ediliyor: {project.title}")
        
        # Proje detaylarını ve raporunu oku
        summary_prompt = f"""
        Aşağıdaki TAMAMLANMIŞ projeyi analiz et ve gelecekteki benzer görevler için 'Altın Kurallar' (Best Practices) veya 'Hata Desenleri' (Anti-Patterns) çıkar.
        
        PROJE: {project.title}
        AÇIKLAMA: {project.description}
        FİNAL RAPORU: {project.report}
        
        Yanıtı şu JSON formatında ver:
        {{
            "ki_title": "Kısa ve öz başlık",
            "category": "technical|operational|strategic",
            "lessons_learned": ["ders 1", "ders 2"],
            "anti_patterns": ["kaçınılması gereken 1"],
            "success_metrics": "Projeyi başarılı kılan temel faktör"
        }}
        """
        
        try:
            response = await self.model_orch.complete_task(
                agent_role="consolidator",
                prompt=summary_prompt,
                system_prompt="Sen bir AGI Hafıza Stratejistisin. Deneyimleri kalıcı bilgeliğe dönüştürürsün."
            )
            
            ki_data = self._parse_json(response.content)
            if ki_data:
                await self._save_knowledge_item(ki_data, project.id)
                
        except Exception as e:
            _log.error(f"[CONSOLIDATOR] Proje konsolidasyon hatası ({project.id}): {e}")

    async def _save_knowledge_item(self, data: Dict[str, Any], source_id: uuid.UUID):
        """Sentezlenen bilgiyi fiziksel bir KI dosyası olarak kaydeder."""
        ki_id = str(uuid.uuid4())[:8]
        filename = f"ki_{data['category']}_{ki_id}.md"
        path = os.path.join(self.knowledge_dir, filename)
        
        content = f"""# Knowledge Item: {data['ki_title']}

- **ID**: {ki_id}
- **Kaynak Proje**: {source_id}
- **Kategori**: {data['category']}
- **Oluşturulma**: {datetime.now(timezone.utc).isoformat()}

## Öğrenilen Dersler
{chr(10).join([f"- {l}" for l in data['lessons_learned']])}

## Anti-Pattern'ler (Kaçınılması Gerekenler)
{chr(10).join([f"- {a}" for a in data['anti_patterns']])}

## Başarı Faktörü
{data['success_metrics']}
"""
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        
        _log.info(f"[CONSOLIDATOR] Yeni Bilgi Öğesi (KI) kaydedildi: {filename}")

    def _parse_json(self, text: str) -> Optional[Dict]:
        import re
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
        return None

# --- Background Task Definition ---
async def start_consolidation_loop():
    from core.agi.monitoring.token_budgeter import token_budgeter
    consolidator = Consolidator()
    
    while True:
        try:
            # ── ADAPTIVE SLEEP (Phase 24) ──
            health = await token_budgeter.check_health()
            score = health["health_score"]
            
            if score > 0.8:
                delay = 3600 * 12 # 12 saat (Normal)
            elif score > 0.4:
                delay = 86400 * 3  # 3 gün (Stressed)
            else:
                delay = 86400 * 7 # 1 hafta (Critical)
                _log.warning(f"[CONSOLIDATOR] Metabolizma kısıtlı, konsolidasyon yavaşlatıldı: {delay}s")

            await consolidator.run_consolidation_cycle()
            await asyncio.sleep(delay)
            
        except Exception as e:
            _log.error(f"[CONSOLIDATOR] Background loop error: {e}")
            await asyncio.sleep(600)
