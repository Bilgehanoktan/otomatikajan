import os
import json
import glob
from typing import List, Dict, Any, Optional
from packages.observability.logging import get_logger
from packages.orchestration.indexing.system_indexer import SystemIndexer
from packages.persistence.session import session_scope
from packages.persistence.repository import ProjectRepository

_log = get_logger("agi_memory_api")

class MemoryAPI:
    """
    AGI'nin birleşik bilişsel hafıza arayüzü.
    Kod tabanı (Indexer), Geçmiş (Project Logs) ve Bilgelik (KIs) arasında köprü kurar.
    """
    
    def __init__(self):
        self.indexer = SystemIndexer()
        self.knowledge_dir = "knowledge"

    async def get_strategic_context(self, query: str, limit: int = 5) -> str:
        """
        Belirli bir konu için tüm hafıza katmanlarından stratejik bağlam toplar.
        """
        _log.info(f"[MEMORY-API] Stratejik bağlam aranıyor: {query}")
        
        # 1. Kod Tabanı Bağlamı (Indexer)
        code_context = self.indexer.get_context_for_task(query=query, limit=3)
        
        # 2. Deneyim Bağlamı (Project Logs)
        from packages.persistence.models import ProjectStatus
        async with session_scope() as db:
            past_projects = await ProjectRepository.list_recent(db, limit=3, search=query, status=ProjectStatus.COMPLETED.value)
            project_context = "\n".join([f"- {p.title}: {p.report if p.report else 'Rapor yok'}" for p in past_projects])
            
        # 3. Bilgelik Bağlamı (Knowledge Items)
        ki_context = self._search_knowledge_items(query, limit=2)
        
        full_context = f"""
        --- BİRLEŞİK AGİ HAFIZASI ---
        
        [STRATEJİK BİLGİ (KNOWLEDGE ITEMS)]
        {ki_context if ki_context else 'Yeni bilgi öğesi bulunamadı.'}
        
        [GEÇMİŞ DENEYİM (PROJECT LOGS)]
        {project_context if project_context else 'Geçmiş deneyim bulunamadı.'}
        
        [MEVCUT KOD YAPISI (SYSTEM INDEX)]
        {code_context}
        """
        
        return full_context[:8000] # Token limitini korumak için kırp

    def _search_knowledge_items(self, query: str, limit: int = 3) -> str:
        """Knowledge Items dizininde basit anahtar kelime araması yapar."""
        if not os.path.exists(self.knowledge_dir):
            return ""
            
        ki_files = glob.glob(os.path.join(self.knowledge_dir, "*.md"))
        matches = []
        
        query_l = query.lower()
        for fpath in ki_files:
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
                    if query_l in content.lower():
                        matches.append(content[:500]) # Sadece giriş kısmını al
            except Exception as e:
                _log.error(f"KI okuma hatası: {e}")
                
        return "\n\n".join(matches[:limit])

# --- Singleton Export ---
memory_api = MemoryAPI()
