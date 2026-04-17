import asyncio
import uuid
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pathlib import Path

from services.observability.logging import get_logger
from libs.llm.model_orchestrator import ModelOrchestrator
from services.orchestration.application.self_updater import SelfUpdater
from services.governance.lineage_service import LineageService
from services.improve.repair_bench import RepairBenchService
from libs.db.session import AsyncSessionLocal
from libs.governance.constitutional_guard import ConstitutionalGuard
from services.governance.budget_service import BudgetService
from libs.llm.cost_tracker import CostTracker
from libs.config import MONTHLY_BUDGET
from libs.llm.model_router import TaskComplexity

logger = get_logger("improve.evolution_orchestrator")

class AutonomousEvolutionOrchestrator:
    """
    Sürekli Otonom Gelişim Orkestratörü.
    Döngü: Planla -> Test Et -> Kaydet -> Tekrarla.
    """

    def __init__(self, model_orch: ModelOrchestrator, project_root: str):
        self.model_orch = model_orch
        self.project_root = Path(project_root)
        self.self_updater = SelfUpdater(model_orch, project_root)
        self.lineage_service = LineageService()
        from services.improve.self_tuning_engine import SelfTuningEngine
        self.tuning_engine = SelfTuningEngine(RepairBenchService(model_orch))
        self.guard = ConstitutionalGuard(project_root)
        self.cost_tracker = CostTracker()
        
        self.is_running = False
        self.failure_counter: Dict[str, int] = {}
        self.STUCK_THRESHOLD = 3
        self.DAILY_BUDGET_PERCENT = 0.05  # %5 günlük limit
        self.loop_delay = 300  # 5 dakika

    async def start(self):
        """Evrim döngüsünü başlatır."""
        if self.is_running:
            return
        self.is_running = True
        logger.info("🚀 Autonomous Evolution Loop STARTED.")
        asyncio.create_task(self._run_loop())

    async def stop(self):
        """Evrim döngüsünü durdurur."""
        self.is_running = False
        logger.info("🛑 Autonomous Evolution Loop STOPPED.")

    async def _run_loop(self):
        while self.is_running:
            try:
                logger.info("--- New Evolution Cycle Starting ---")
                
                # 0. BÜTÇE KONTROLÜ (Institutional Governing Circuit Breaker)
                # Global bütçeyi kontrol ediyor (System Project ID: sovereign-system)
                if not await BudgetService.check_circuit_breaker("sovereign-system", 0.01):
                    logger.warning("⚠️ Institutional budget circuit breaker ACTIVE. Evolution paused.")
                    await asyncio.sleep(self.loop_delay * 5)
                    continue

                # 1. PLANLA
                plan = await self._generate_evolution_plan()
                if not plan:
                    logger.info("No evolution candidates identified. Sleeping...")
                    await asyncio.sleep(self.loop_delay)
                    continue

                target_file = plan.get("target_file")
                instruction = plan.get("instruction")
                rationale = plan.get("rationale", "Autonomous Growth Pulse")

                # 1.1 ANAYASAL KORUMA KONTROLÜ
                if self.guard.is_locked(target_file):
                    logger.error(f"❌ CONSTITUTIONAL LOCK: Modification of {target_file} is forbidden.")
                    await self.lineage_service.log_decision(
                        decision_type="BLOCK_PROTECTED",
                        component_name=target_file,
                        rationale="Attempted to modify a constitutionally protected path.",
                        meta_data={"plan": plan}
                    )
                    await asyncio.sleep(self.loop_delay)
                    continue

                logger.info(f"📍 Plan: {target_file} -> {instruction[:50]}...")

                # 2. TEST ET & UYGULA (SelfUpdater zaten shadow test yapar)
                result_msg = await self.self_updater.modify_system_file(
                    target_file_path=target_file,
                    instruction=instruction
                )

                # 3. KAYDET
                success = "Başarılı" in result_msg
                await self.lineage_service.log_decision(
                    decision_type="SYSTEM_EVOLUTION",
                    component_name=target_file,
                    rationale=f"{rationale} | Result: {result_msg}",
                    trigger_event={"source": "evolution_loop", "plan": plan},
                    meta_data={"success": success, "output": result_msg}
                )

                # 4. TAKILMA (STUCK) KONTROLÜ
                if not success:
                    self.failure_counter[target_file] = self.failure_counter.get(target_file, 0) + 1
                    if self.failure_counter[target_file] >= self.STUCK_THRESHOLD:
                        await self._diagnose_and_unstick(target_file, result_msg)
                else:
                    self.failure_counter[target_file] = 0 # Reset on success

                logger.info(f"✔️ Cycle complete: {result_msg}")

            except Exception as e:
                logger.error(f"Critical error in evolution loop: {e}")
            
            await asyncio.sleep(self.loop_delay)



    async def _generate_evolution_plan(self) -> Optional[Dict[str, Any]]:
        """Sistemin neresini geliştireceğine karar verir."""
        todos = self._scan_for_todos()
        
        prompt = f"""
SİSTEM EVRİM PLANI OLUŞTURUCU
Proje Kökü: {self.project_root}
Bulunan TODO'lar: {todos[:10]}

GÖREV: Sistemin kod kalitesini, performansını veya yönetişim bütünlüğünü artıracak BİR ADET kritik geliştirme seç.
Dönüş Formatı (Sadece JSON):
{{
  "target_file": "dosya/yolu.py",
  "instruction": "şunu ekle/düzelt",
  "rationale": "niye bunu yapıyoruz",
  "priority": "high/medium/low"
}}
"""
        try:
            response = await self.model_orch.complete(
                messages=[{"role": "user", "content": prompt}],
                preferred_agent="engineering-system-architect"
            )
            content = response.content if hasattr(response, 'content') else str(response)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            import json
            return json.loads(content)
        except Exception as e:
            logger.error(f"Failed to generate evolution plan: {e}")
            return None

    def _scan_for_todos(self) -> List[str]:
        """Basit bir TODO taraması yapar."""
        results = []
        for root, dirs, files in os.walk(self.project_root):
            if any(d in root for d in [".git", "node_modules", "workspace", "artifacts"]):
                continue
            for file in files:
                if file.endswith(".py"):
                    p = Path(root) / file
                    try:
                        content = p.read_text(encoding="utf-8")
                        if "TODO" in content or "FIXME" in content:
                            results.append(str(p.relative_to(self.project_root)))
                    except:
                        continue
        return results

    async def _diagnose_and_unstick(self, target_file: str, last_error: str):
        """Tıkanma durumunda 3-tier kurtarma politikası uygular."""
        failures = self.failure_counter.get(target_file, 0)
        
        if failures == 1:
            logger.warning(f"⚠️ STUCK T1: {target_file}. Record logged.")
        elif failures == 2:
            logger.warning(f"⚠️ STUCK T2: Deep Diagnosis for {target_file}.")
            diagnosis = await self._run_deep_diagnosis(target_file, last_error)
            logger.info(f"Deep Diagnosis Result: {diagnosis[:100]}...")
        else:
            logger.error(f"🚨 STUCK T3: QUARANTINE ACTIVE for {target_file}!")
            await self.lineage_service.log_decision(
                decision_type="QUARANTINE_LOCKED",
                component_name=target_file,
                rationale=f"Multiple consecutive failures ({failures}). Operator intervention required.",
                meta_data={"last_error": last_error}
            )
            self.failure_counter[target_file] = 999 

    async def _run_deep_diagnosis(self, target_file: str, last_error: str) -> str:
        """Güçlü bir model (REASONING tier) ile sorunun köküne iner."""
        prompt = f"DEEP DIAGNOSIS: {target_file} continues to fail shadow tests with error: {last_error}. Analyze root cause and suggest logic structural change."
        try:
            # Phase 30: Use REASONING tier for deep diagnosis
            response = await self.model_orch.complete(
                messages=[{"role": "user", "content": prompt}],
                task_complexity=TaskComplexity.REASONING.value
            )
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            logger.error(f"Deep diagnosis failed: {e}")
            return "Diagnosis failed."

# Global instance for easy access
evolution_orchestrator = None

def init_evolution_orchestrator(model_orch, project_root):
    global evolution_orchestrator
    evolution_orchestrator = AutonomousEvolutionOrchestrator(model_orch, project_root)
    return evolution_orchestrator
