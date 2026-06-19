import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone

# Proje kök dizinini ekle
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from services.orchestration.ceo.optimizer import CEOStochasticOptimizer
from libs.llm.model_orchestrator import ModelOrchestrator
from libs.db.session import session_scope
from libs.db.models import SovereignModelPolicy, LLMCostLog, ModelBenchmarking

async def verify_optimizer():
    print("--- CEO Optimizer Verification ---")
    
    async with session_scope() as db:
        # 1. Mock Data Injection (Slow Provider)
        print("1. Mock veri enjekte ediliyor (High Latency)...")
        log = LLMCostLog(
            provider="openai",
            model="gpt-4o",
            agent_id="test_agent",
            agent_role="architect",
            latency_s=8.5, # 8.5 saniye (Yavaş)
            success=True,
            created_at=datetime.now(timezone.utc)
        )
        db.add(log)
        await db.commit()
    
    # 2. Run Optimization Cycle
    print("2. Optimizasyon döngüsü çalıştırılıyor...")
    await CEOStochasticOptimizer.run_optimization_cycle()
    
    # 3. Check Policy
    async with session_scope() as db:
        from sqlalchemy import select
        res = await db.execute(select(SovereignModelPolicy).where(SovereignModelPolicy.agent_role == "architect"))
        policy = res.scalars().first()
        
        if not policy:
            print("(!) Mevcut politika yoktu, test için manuel ekleniyor.")
            policy = SovereignModelPolicy(
                agent_role="architect", 
                winner_provider="openai", 
                runner_up="gemini", 
                fallback_chain=["openai", "gemini"]
            )
            db.add(policy)
            await db.commit()
            
            # Tekrar döngü çalıştır (Benchmark güncellendiği için şimdi policy güncellenmeli)
            await CEOStochasticOptimizer.run_optimization_cycle()
            await db.refresh(policy)
            
        print(f"[OK] Politika Durumu: Winner {policy.winner_provider} | Runner-up: {policy.runner_up}")

    # 4. Verify ModelOrchestrator
    print("4. ModelOrchestrator hiyerarşisi doğrulanıyor...")
    orch = ModelOrchestrator()
    chain = await orch.get_fallback_chain("architect")
    print(f"[OK] Fallback Zinciri: {chain}")
    
    if chain[0] == "gemini":
        print("SUCCESS: Yavaş 'openai' yerine 'gemini' başa alındı!")
    else:
        print("ERROR: Model hiyerarşisi değişmedi.")

if __name__ == "__main__":
    asyncio.run(verify_optimizer())
