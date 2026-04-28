import asyncio
import json
import os
from sqlalchemy import select, func, desc, update, case
from typing import List, Dict, Any, Optional
from services.observability.logging import get_logger
from services.orchestration.indexing.system_indexer import SystemIndexer
from libs.llm.model_orchestrator import ModelOrchestrator
from libs.db.session import session_scope
from libs.db.repositories.repository import ImprovementRepository, EventLogRepository
from services.orchestration.application.self_updater import SelfUpdater

_log = get_logger("agi_architect")

class Architect:
    """
    Sistemin yapısal sağlığını denetleyen ve yeni alt sistemler/refaktörler 
    sentezleyen 'Kıdemli Sistem Tasarımcısı' düğümü.
    """
    
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()
        self.indexer = SystemIndexer()
        self.complexity_threshold_kb = 15  # 15KB üzerindeki dosyalar bölünebilir
        self.symbol_threshold = 25        # 25'ten fazla sembol içeren dosyalar karmaşıktır

    async def scan_architecture(self):
        """Kod tabanını tarar, mimari ve bilişsel borçları tespit eder."""
        _log.info("[ARCHITECT] Mimari ve Bilişsel tarama başlatıldı.")
        await self._scan_structural_debt()
        await self._scan_cognitive_debt()

    async def _scan_structural_debt(self):
        index_data = self.indexer.read_index()
        entries = index_data.get("entries", [])
        debt_found = []
        for entry in entries:
            path = entry["path"]
            size_kb = entry["size_bytes"] / 1024
            symbols_count = len(entry["symbols"])
            if size_kb > self.complexity_threshold_kb or symbols_count > self.symbol_threshold:
                debt_found.append({
                    "path": path,
                    "size_kb": round(size_kb, 1),
                    "symbols": symbols_count,
                    "summary": entry["summary"][:200]
                })
        if not debt_found:
            _log.info("[ARCHITECT] Belirgin bir yapısal borç tespit edilmedi.")
            return
        await self._synthesize_refactor_proposals(debt_found)

    async def _synthesize_refactor_proposals(self, debt: List[Dict[str, Any]]):
        prompt = f"""
        Aşağıdaki dosyalar sistemde 'Yapısal Borç' (Architectural Debt) olarak işaretlendi. 
        Bunları bölmek veya yeni bir modüler yapıya (service/layer) taşımak için mimari bir plan oluştur.
        KARMASIK DOSYALAR: {json.dumps(debt, indent=2)}
        Yanıtı JSON formatında (ArchitectureProposal) ver.
        """
        try:
            response = await self.model_orch.complete_task(agent_role="architect", prompt=prompt)
            proposal = self._parse_json(response.content)
            if proposal: await self._report_architecture_opportunity(proposal)
        except Exception as e: _log.error(f"[ARCHITECT] Sentez hatası: {e}")

    async def _report_architecture_opportunity(self, proposal: Dict[str, Any]):
        async with session_scope() as db:
            await ImprovementRepository.create(
                db, title=f"ARCHITECTURE: {proposal['title']}", description=proposal['reasoning'],
                source_type="architectural_scan", category="architecture", severity="medium", impact_score=0.7,
                evidence=json.dumps(proposal["actions"])
            )
            await EventLogRepository.write(db, event_type="architecture_proposal_generated", severity="info", phase="architecture", message=f"Mimari Refaktör Önerisi: {proposal['title']}", payload=proposal)

    async def _scan_cognitive_debt(self):
        from libs.db.models import SkillExecutionLog
        async with session_scope() as db:
            q = select(SkillExecutionLog.agent_id, func.count(SkillExecutionLog.id).label("total"), func.sum(case((SkillExecutionLog.success == False, 1), else_=0)).label("failures")).group_by(SkillExecutionLog.agent_id).having(func.count(SkillExecutionLog.id) > 5).order_by(desc("failures"))
            result = await db.execute(q)
            for s in result.all():
                failure_rate = s.failures / s.total
                if failure_rate > 0.4: await self._propose_source_refactor(s.agent_id, failure_rate)

    async def _propose_source_refactor(self, agent_id: str, failure_rate: float):
        potential_path = f"agents/{agent_id}.py"
        if not os.path.exists(potential_path): return
        with open(potential_path, "r", encoding="utf-8") as f: source_code = f.read()
        prompt = f"Ajan {agent_id} %{failure_rate*100:.1f} hata oranına sahip. Refaktör planla."
        try:
            response = await self.model_orch.complete_task(agent_role="architect", prompt=prompt)
            proposal = self._parse_json(response.content)
            if proposal:
                await self._report_refactor_opportunity(proposal)
                if failure_rate > 0.6: await self._apply_autonomous_refactor(proposal, potential_path)
        except Exception as e: _log.error(f"[ARCHITECT] Bilişsel refaktör hatası: {e}")

    async def _apply_autonomous_refactor(self, proposal: Dict[str, Any], file_path: str):
        updater = SelfUpdater()
        new_code = proposal.get("suggested_refactor")
        if not new_code or "import" not in new_code: return
        try:
            updater._atomic_write_text(file_path, new_code)
            _log.info(f"[ARCHITECT] Otonom yama uygulandı: {file_path}")
        except Exception as e: _log.error(f"[ARCHITECT] Yama hatası: {e}")

    async def _report_refactor_opportunity(self, proposal: Dict[str, Any]):
        async with session_scope() as db:
            await ImprovementRepository.create(db, title=f"COGNITIVE REFACTOR: {proposal['agent_id']}", description=proposal['reasoning'], source_type="cognitive_scan", category="code_quality", severity="high", impact_score=0.9, evidence=json.dumps(proposal))

    async def decompose(self, prompt: str) -> str:
        try:
            res = await self.model_orch.complete_task(agent_role="architect", prompt=prompt, system_prompt="Sen bir AGI Master Planner'sın. JSON döndür.")
            return res.content
        except: return "[]"

    async def refactor_plan(self, prompt: str) -> str:
        try:
            res = await self.model_orch.complete_task(agent_role="architect", prompt=prompt)
            return res.content
        except: return "Error"

    async def forge_specialist_prompt(self, role: str, task_context: str) -> str:
        prompt = f"Rol: {role}\nBağlam: {task_context}\nSistem promptu hazırla."
        try:
            res = await self.model_orch.complete_task(agent_role="architect", prompt=prompt)
            return res.content
        except: return f"Sen {role} konusunda uzmansın."

    async def recalibrate_reasoning(self, report: Dict[str, Any]):
        prompt = f"Bilişsel puan düştü: {json.dumps(report, indent=2)}. Plan hazırla."
        try:
            res = await self.model_orch.complete_task(agent_role="architect", prompt=prompt)
            await self._report_refactor_opportunity({"agent_id": "cognitive_core", "reasoning": "Performance drop", "suggested_refactor": res.content})
        except: pass

    def _parse_json(self, text: str) -> Optional[Dict]:
        import re
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try: return json.loads(match.group())
            except: pass
        return None

# Lazy Singleton — prevent import-time crash from ModelOrchestrator init
_architect_instance: Optional[Architect] = None

def get_architect(model_orch: Optional[ModelOrchestrator] = None) -> Architect:
    global _architect_instance
    if _architect_instance is None:
        _architect_instance = Architect(model_orch=model_orch)
    return _architect_instance

# Backward compatibility alias (lazy)
class _LazyArchitect:
    def __getattr__(self, name):
        return getattr(get_architect(), name)

architect = _LazyArchitect()

async def start_architect_scan_loop():
    while True:
        try:
            await get_architect().scan_architecture()
            await asyncio.sleep(3600 * 24)
        except Exception as e:
            _log.error(f"[ARCHITECT] Loop hatasi: {e}")
            await asyncio.sleep(600)
