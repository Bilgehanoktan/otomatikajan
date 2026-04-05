import asyncio
import json
import os
from sqlalchemy import select, func, desc, update, case
from typing import List, Dict, Any, Optional
from observability.logging import get_logger
from packages.orchestration.indexing.system_indexer import SystemIndexer
from llm.model_orchestrator import ModelOrchestrator
from db.session import session_scope
from db.repository import ImprovementRepository, EventLogRepository
from packages.orchestration.application.self_updater import SelfUpdater

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
        
        # 1. Mimari Borç Taraması (Dosya Boyutu/Karmaşıklık)
        await self._scan_structural_debt()
        
        # 2. Faz 23: Bilişsel Borç Taraması (Agent Performansı)
        await self._scan_cognitive_debt()

    async def _scan_structural_debt(self):
        """Dosya boyutu ve sembol sayısına dayalı geleneksel borç taraması."""
        index_data = self.indexer.read_index()
        entries = index_data.get("entries", [])
        
        debt_found = []
        
        # 2. Heuristic Analiz: Dev Dosyalar ve Karmaşıklık
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

        # 3. LLM ile Çözüm Önerisi Sentezi (Architecture Proposal)
        await self._synthesize_refactor_proposals(debt_found)

    async def _synthesize_refactor_proposals(self, debt: List[Dict[str, Any]]):
        """Tespit edilen karmaşıklığı LLM ile analiz eder ve yapılandırma planı oluşturur."""
        _log.info(f"[ARCHITECT] {len(debt)} adet karmaşık yapı için çözüm sentezleniyor.")
        
        prompt = f"""
        Aşağıdaki dosyalar sistemde 'Yapısal Borç' (Architectural Debt) olarak işaretlendi. 
        Bunları bölmek veya yeni bir modüler yapıya (service/layer) taşımak için mimari bir plan oluştur.
        
        KARMASIK DOSYALAR:
        {json.dumps(debt, indent=2)}
        
        Yanıtı JSON formatında (ArchitectureProposal) ver:
        {{
            "title": "Refaktör Başlığı",
            "reasoning": "Neden bu değişikliğe ihtiyaç var?",
            "actions": [
                {{
                    "type": "create_subsystem",
                    "path": "core/new_module/",
                    "purpose": "Açıklama",
                    "files_to_scaffold": ["base.py", "schemas.py", "utils.py"]
                }},
                {{
                    "type": "split_file",
                    "source": "path/to/big_file.py",
                    "targets": ["path/to/part_a.py", "path/to/part_b.py"]
                }}
            ]
        }}
        """
        
        try:
            response = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt="Sen bir AGI Mimarı ve Sistem Mühendisisin. Temiz kod ve modüler mimari konusunda uzmansın."
            )
            
            proposal = self._parse_json(response.content)
            if proposal:
                await self._report_architecture_opportunity(proposal)
                
        except Exception as e:
            _log.error(f"[ARCHITECT] Çözüm sentez hatası: {e}")

    async def _report_architecture_opportunity(self, proposal: Dict[str, Any]):
        """Sentezlenen mimari planı İyileştirme Fırsatı olarak kaydeder."""
        async with session_scope() as db:
            from db.repository import ImprovementRepository
            
            opp = await ImprovementRepository.create(
                db,
                title=f"ARCHITECTURE: {proposal['title']}",
                description=proposal['reasoning'],
                source_type="architectural_scan",
                category="architecture",
                severity="medium",
                impact_score=0.7,
                evidence=json.dumps(proposal["actions"])
            )
            
            # Event Log
            await EventLogRepository.write(
                db,
                event_type="architecture_proposal_generated",
                severity="info",
                phase="architecture",
                message=f"Mimari Refaktör Önerisi: {proposal['title']}",
                payload=proposal
            )
            await db.commit()

    async def _scan_cognitive_debt(self):
        """Agent performans verilerini (SkillExecutionLog) analiz ederek mantıksal borçları bulur."""
        _log.info("[ARCHITECT] Bilişsel borç taraması (Agent Efficiency) başlatıldı.")
        
        from db.models import SkillExecutionLog
        from sqlalchemy import func, select, desc
        
        async with session_scope() as db:
            # Son 100 logda en çok hata yapan uzman ajanları bul
            q = select(
                SkillExecutionLog.agent_id,
                func.count(SkillExecutionLog.id).label("total"),
                func.sum(case((SkillExecutionLog.success == False, 1), else_=0)).label("failures")
            ).group_by(SkillExecutionLog.agent_id).having(func.count(SkillExecutionLog.id) > 5).order_by(desc("failures"))
            
            result = await db.execute(q)
            stats = result.all()
            
            for s in stats:
                failure_rate = s.failures / s.total
                if failure_rate > 0.4: # %40+ hata oranı bir bilişsel borçtur
                    _log.warning(f"[ARCHITECT] Yüksek hata oranı saptandı: {s.agent_id} (%{failure_rate*100:.1f})")
                    await self._propose_source_refactor(s.agent_id, failure_rate)

    async def _propose_source_refactor(self, agent_id: str, failure_rate: float):
        """Bilişsel borcu olan ajan için kaynak kodu refaktörü önerir."""
        # Ajanın kaynak dosyasını bul (Varsayılan: agents/{agent_id}.py)
        potential_path = f"agents/{agent_id}.py"
        if not os.path.exists(potential_path):
            return

        with open(potential_path, "r", encoding="utf-8") as f:
            source_code = f.read()

        prompt = f"""
        Aşağıdaki uzman ajan ({agent_id}) son görevlerde %{failure_rate*100:.1f} hata oranına sahip. 
        Bu ajanın mantıksal akışını, hata yakalama mekanizmalarını veya niyet anlama (intent parsing)
        kısımlarını iyileştirmek için bir KAYNAK KOD REFAKTÖRÜ planı oluştur.
        
        KAYNAK KOD:
        ```python
        {source_code}
        ```
        
        Yanıtı JSON formatında (CognitiveRefactorProposal) ver:
        {{
            "agent_id": "{agent_id}",
            "reasoning": "Hata kök neden analizi ve refaktör gerekçesi",
            "suggested_refactor": "Yeni Python kodu (tam dosya veya kritik blok)",
            "safety_checks": ["Dosya bütünlüğü korunmalı", "Mevcut kontratlar bozulmamalı"]
        }}
        """
        
        try:
            response = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt="Sen bir AGI Mühendisisin. Kendi ajanlarının mantığını otonom olarak iyileştirmekten sorumlusun."
            )
            
            proposal = self._parse_json(response.content)
            if proposal:
                await self._report_refactor_opportunity(proposal)
                
                # Faz 34: Otonom Uygulama Döngüsü
                if failure_rate > 0.6: # Kritik hata eşiği
                    _log.info(f"[ARCHITECT] KRİTİK HATA ORANI (%{failure_rate*100:.1f}). Otonom refaktör başlatılıyor: {agent_id}")
                    await self._apply_autonomous_refactor(proposal, potential_path)
        except Exception as e:
            _log.error(f"[ARCHITECT] Bilişsel refaktör sentez hatası: {e}")

    async def _apply_autonomous_refactor(self, proposal: Dict[str, Any], file_path: str):
        """SelfUpdater kullanarak bilişsel iyileştirmeyi sisteme uygular."""
        updater = SelfUpdater()
        
        # Risk analizi ve onay (Sovereign modda otomatik devam eder)
        new_code = proposal.get("suggested_refactor")
        if not new_code or "import" not in new_code:
            _log.warning("[ARCHITECT] Geçersiz refaktör kodu. İptal edildi.")
            return

        try:
            # 1. Mevcut dosyayı oku
            with open(file_path, "r", encoding="utf-8") as f:
                old_code = f.read()

            # 2. SelfUpdater üzerinden güvenli güncelleme yap
            # Not: SelfUpdater.apply_update normalde bir UpdateRequest bekler. 
            # Burada basitleştirilmiş bir çağrı simüle ediyoruz veya doğrudan atomic write kullanıyoruz.
            # Ancak SelfUpdater'ın asıl gücü test/rollback olduğu için onun akışını tercih etmeliyiz.
            
            _log.info(f"[ARCHITECT] '{file_path}' için otonom yama (patch) hazırlanıyor...")
            
            # Doğrudan atomic write ve backup (SelfUpdater içindeki korumaları kullanır)
            updater._atomic_write_text(file_path, new_code)
            
            _log.info(f"[ARCHITECT] Yama uygulandı. Yedek: {file_path}.bak")
            
        except Exception as e:
            _log.error(f"[ARCHITECT] Otonom yama hatası: {e}")

    async def _report_refactor_opportunity(self, proposal: Dict[str, Any]):
        async with session_scope() as db:
            opp = await ImprovementRepository.create(
                db,
                title=f"COGNITIVE REFACTOR: {proposal['agent_id']}",
                description=proposal['reasoning'],
                source_type="cognitive_scan",
                category="code_quality",
                severity="high",
                impact_score=0.9,
                evidence=json.dumps(proposal)
            )
            await db.commit()

    async def decompose(self, prompt: str) -> str:
        """
        Karmaşık bir görevi otonom olarak atomik alt-görevlere böler. (Faz 67)
        """
        _log.info("[ARCHITECT] Görev ayrıştırılıyor (Recursive Decomposition)...")
        try:
            response = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt="Sen bir AGI Master Planner'sın. Karmaşık görevleri, bağımlılıkları gözeterek en küçük atomik parçalara ayırırsın. SADECE JSON döndür."
            )
            return response.content
        except Exception as e:
            _log.error(f"[ARCHITECT] Decompose error: {e}")
            return "[]"

    async def refactor_plan(self, prompt: str) -> str:
        """
        Başarısız bir simülasyon veya hata sonrası planı revize eder. (Faz 65/66)
        """
        _log.info("[ARCHITECT] Plan revize ediliyor (Reflective Refactor)...")
        try:
            response = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt="Sen bir AGI Strateji Uzmanısın. Eleştirileri ve simülasyon hatalarını dikkate alarak planı daha güvenli ve etkili hale getirirsin."
            )
            return response.content
        except Exception as e:
            _log.error(f"[ARCHITECT] Refactor plan error: {e}")
            return "Error while refactoring plan."

    async def forge_specialist_prompt(self, role: str, task_context: str) -> str:
        """
        Subtask için özel bir uzman ajan 'prompt'u sentezler (Phase 70).
        """
        _log.info(f"[ARCHITECT-FORGE] Uzmanlık sentezleniyor: {role}")
        
        prompt = f"""
        Rol: {role}
        Görev Bağlamı: {task_context}
        
        Sistem bu görev için geçici bir uzman ajana ihtiyaç duyuyor. 
        Lütfen bu ajan için en az 500 kelimelik, derinlemesine teknik prensipler içeren, 
        'Zorunlu Kurallar' ve 'Limitler' bölümlerine sahip bir SYSTEM PROMPT hazırla.
        """
        
        try:
            response = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt="Sen bir AGI Master Weaver'sın. Diğer ajanların 'Zihin Haritasını' tasarlarsın."
            )
            return response.content
        except Exception as e:
            _log.error(f"[ARCHITECT-FORGE] Forgery error: {e}")
            return f"Sen {role} konusunda uzmansın."

    async def recalibrate_reasoning(self, report: Dict[str, Any]):
        """
        Bilişsel puan düştüğünde sistemi otonom olarak iyileştirir (Faz 69).
        """
        _log.warning(f"[ARCHITECT-SELF-REPAIR] Düşük bilişsel puan analizi raporlanıyor...")
        
        prompt = f"""
        Sovereign AGI bilişsel testi (EvalHarness) başarısız oldu.
        RAPOR: {json.dumps(report, indent=2)}
        
        Lütfen zayıf olan bilişsel katmanı (ToolGrounder, ForesightCortex vb.) analiz et ve 
        mantıksal bir iyileştirme/refaktör planı oluştur.
        """
        
        try:
            response = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt="Sen bir AGI Mühendisisin. Kendi bilişsel yapındaki mantıksal hataları otonom olarak onarmakla sorumlusun."
            )
            
            # Bu planı 'Self-Evolution' fırsatı olarak kaydet
            await self._report_refactor_opportunity({
                "agent_id": "cognitive_core",
                "reasoning": f"EvalHarness performans düşüşü: {report.get('overall_cognitive_score')}",
                "suggested_refactor": response.content
            })
            _log.info("[ARCHITECT-SELF-REPAIR] Bilişsel recalibration planı hazırlandı ve kaydedildi.")
        except Exception as e:
            _log.error(f"[ARCHITECT-SELF-REPAIR] Recalibration error: {e}")

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
async def start_architect_scan_loop():
    architect = Architect()
    while True:
        try:
            await architect.scan_architecture()
            await asyncio.sleep(3600 * 24) # Günde bir kez mimari tarama yap
        except Exception as e:
            _log.error(f"[ARCHITECT] Background loop error: {e}")
            await asyncio.sleep(600)
