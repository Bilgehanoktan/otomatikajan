import os
from typing import Optional, List, Dict, Any
from packages.orchestration.agi.schemas import ProblemFrame, ContextPackage
from llm.model_orchestrator import ModelOrchestrator
from observability.logging import get_logger

_log = get_logger("agi_perception_gate")

class PerceptionGate:
    """
    Cognitive Core (Katman 3): Active Perception / Epistemic Agency.
    Sistemin 'ne bilmediğini sorgulamasını' ve eksik bağlamı araştırmasını sağlar.
    """
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()

    async def probe(self, frame: ProblemFrame, current_context: str) -> str:
        """
        Girdideki belirsizlikleri tespit eder ve gerekirse otonom araştırma yapar.
        """
        if frame.ambiguity_score < 0.3:
            return "" # Bağlam yeterli görünüyor
            
        _log.info(f"Yüksek Belirsizlik Tespit Edildi ({frame.ambiguity_score}). Aktif Algı tetikleniyor...")
        
        # 1. Eksik ne? Sorusu (Epistemic Questioning)
        prompt = f"""
        Şu hedefe ulaşmak için hangi dosyaları veya kod bloklarını incelemem gerek?
        HEDEF: {frame.objective}
        MEVCUT BAĞLAM: {current_context[:500]}...
        
        Gereken araştırma adımlarını JSON formatında liste:
        {{
            "investigations": [
                {{ "type": "grep", "query": "pattern", "path": "." }},
                {{ "type": "list_dir", "path": "path" }}
            ]
        }}
        """

        try:
            response = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt="Sen bir AGI Algı Kapısı (Perception Gate) bileşenisin. Hedefe ulaşmak için neyi bilmediğini tespit etmelisin."
            )
            
            research_data = self._parse_json(response.content)
            enriched_context = []
            
            # 2. Otonom Araştırma (Surgical Search)
            for inv in research_data.get("investigations", []):
                res = await self._run_investigation(inv)
                if res:
                    enriched_context.append(f"RESEARCH_FINDING ({inv['type']}): {res}")
            
            return "\n".join(enriched_context)

        except Exception as e:
            _log.error(f"Perception probe hatası: {e}")
            return ""

    async def _run_investigation(self, inv: Dict[str, Any]) -> str:
        """Dosya sisteminde otonom keşif yapar."""
        inv_type = inv.get("type")
        path = inv.get("path", ".")
        query = inv.get("query", "")
        
        try:
            if inv_type == "list_dir":
                import asyncio
                files = await asyncio.to_thread(os.listdir, path)
                return f"Directory {path} content: {files[:20]}"
            elif inv_type == "grep":
                import asyncio
                def _sync_grep():
                    findings = []
                    for root, _, files in os.walk(path):
                        for f in files:
                            if f.endswith(('.py', '.js', '.ts', '.md', '.txt')):
                                fpath = os.path.join(root, f)
                                try:
                                    with open(fpath, "r", encoding="utf-8", errors="ignore") as fobj:
                                        if query in fobj.read():
                                            findings.append(fpath)
                                            if len(findings) >= 5: return findings
                                except Exception: continue
                    return findings
                
                findings = await asyncio.to_thread(_sync_grep)
                return f"Grep {query} found in: {findings[:5]}"
        except Exception:
            pass
        return ""

    def _parse_json(self, content: str) -> Dict[str, Any]:
        import json
        import re
        match = re.search(r'\{.*\}', content, re.DOTALL)
        return json.loads(match.group()) if match else {}

# Singleton
perception_gate = PerceptionGate()
