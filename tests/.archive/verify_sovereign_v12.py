import asyncio
import unittest
import sys
import os
import time
from unittest.mock import AsyncMock, patch, MagicMock

# Base paths
sys.path.append(os.getcwd())

from packages.orchestration.agi.cognitive.sovereign_cortex import SovereignCortex
from packages.orchestration.agi.task_governance import GovernedTask, SovereignGoal, GovernanceStatus
from packages.orchestration.agi.operational.velocity_engine import EngineResult
from packages.orchestration.agi.operational.kinetic_arbiter import kinetic_arbiter, ArbiterRequest
from packages.orchestration.agi.governance.watchdog import GovernanceWatchdog

class SovereignMasterVerification(unittest.IsolatedAsyncioTestCase):
    """
    Sovereign AGI (v12.12.2) Tam Entegrasyon Dorulama Testi.
    Tm bilisel katmanlarn birbiriyle uyumunu test eder.
    """

    async def asyncSetUp(self):
        print("\n" + "="*50)
        print("SOVEREIGN AGI (v12.12.2) INTEGRATION AUDIT")
        print("="*50)
        await kinetic_arbiter.start()

    async def asyncTearDown(self):
        await kinetic_arbiter.stop()

    async def test_01_full_cognitive_cycle(self):
        """
        Grev Yrtme -> Monologue Kayd -> Dialektik Denetim -> Arbiter Kuyruu
        """
        print("\n[STEP 1] Full Cognitive Cycle & Monologue Persistence")
        cortex = SovereignCortex()
        st = GovernedTask(
            id="master_task_1",
            agent_id="architect",
            prompt="Optimize system kernel",
            status=GovernanceStatus.PENDING,
            internal_monologue="Initial thought: check memory pools."
        )
        parent = SovereignGoal(id="master_goal", title="System Optimization", subtasks=[st])

        # Mocking for all layers
        with patch("packages.orchestration.agi.operational.velocity_engine.velocity_engine.simulate_and_execute", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = EngineResult(
                success=True, 
                output_data="Kernel optimized.",
                reflection="Used pool-based allocation instead of direct malloc."
            )
            
            with patch("packages.orchestration.agi.cognitive.consensus_manager.ConsensusManager.resolve", new_callable=AsyncMock) as mock_consensus:
                mock_consensus.return_value = (True, "Consensus reached with Red-Team audit.")
                
                # Execute node nexus
                await cortex._execute_subtask_nexus(st, parent)
                
                # Verify Monologue Capture
                self.assertEqual(st.internal_monologue, "Used pool-based allocation instead of direct malloc.")
                print("  - Monologue Capture: OK")
                
                # Verify Subconscious Awareness (Check if lesson was discussed - logic check)
                self.assertEqual(st.status, GovernanceStatus.COMPLETED)
                print("  - Nexus Execution: OK")

    async def test_02_resource_arbitration_concurrency(self):
        """Arbiter'ın sıkışık dönemlerde öncelik yönetimi testi."""
        print("\n[STEP 2] Resource Arbitration & Priority Preemption")
        
        # 1. Arbiter'ı temizleyip durduralım
        await kinetic_arbiter.stop()
        await kinetic_arbiter._ensure_queue()
        
        # 2. Manuel Request'ler oluşturalım (Daha düşük sayı = yüksek öncelik)
        # Self Governor: ~-16.5, Tech Writer: ~-3.3
        f_low = asyncio.Future()
        req_low = ArbiterRequest(priority=-3.3, timestamp=time.time(), agent_id="tech_writer", task_id="low_t", future=f_low)
        
        f_high = asyncio.Future()
        req_high = ArbiterRequest(priority=-16.5, timestamp=time.time(), agent_id="self_governor", task_id="high_t", future=f_high)
        
        # Kuyruğa ekle (Sıra farketmez, PrioQueue önceliğe göre çıkarır)
        await kinetic_arbiter._queue.put(req_low)
        await kinetic_arbiter._queue.put(req_high)
        
        # 3. Arbiter'ı başlat (Kısıtlı kapasite)
        kinetic_arbiter._max_total_slots = 1
        kinetic_arbiter._active_slots = 0
        await kinetic_arbiter.start()
        
        print("  - Arbiter started. Expecting Governor (-16.5) to jump ahead of Tech Writer (-3.3)...")
        
        # 4. İlk hangisi onaylandı?
        done, pending = await asyncio.wait([f_low, f_high], return_when=asyncio.FIRST_COMPLETED)
        
        if f_high.done():
            print("  - Arbiter Priority Bypass: OK")
        else:
            self.fail("Tech Writer processed before Governor in congested queue.")

    async def test_03_governance_watchdog_integrity(self):
        """Watchdog'un otonom kural denetimi testi."""
        print("\n[STEP 3] Governance Watchdog & Persistence")
        from packages.orchestration.agi.governance.rules import GovernanceRules
        watchdog = GovernanceWatchdog()
        
        # Mock actual audit logic
        with patch("packages.orchestration.agi.governance.rules.GovernanceRules.audit_project_structure", new_callable=AsyncMock) as mock_audit:
            mock_audit.return_value = [] # No violations
            
            await watchdog.audit_and_repair()
            self.assertEqual(watchdog._last_audit_score, 1.0)
            print(f"  - System Integrity Score: {watchdog._last_audit_score}")
            print("  - Governance Watchdog Audit: OK")

if __name__ == "__main__":
    unittest.main()
